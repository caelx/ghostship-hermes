from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .config import AliasConfig, RouterConfig
from .models import ChatCompletionRequest, ModelCard, ModelsResponse, ReadinessResponse, ResponsesRequest
from .providers.base import ChatProvider, NormalizedProviderError, ProviderChatStreamResult, ProviderModel
from .providers.opencode_zen import OpencodeZenProvider
from .providers.openrouter import OpenRouterProvider
from .state import RouteEvent, SqliteStateStore, StateStore

logger = logging.getLogger("hermes_router")

_ALIASES = ("lightweight", "coding", "heavyweight")

_ALIAS_HINTS: dict[str, tuple[str, ...]] = {
    "lightweight": ("mini", "small", "flash", "flash-lite", "nano", "haiku", "free"),
    "coding": ("coder", "code", "codex", "qwen", "deepseek", "devstral"),
    "heavyweight": ("large", "70b", "72b", "opus", "pro", "reason", "thinking", "sonnet"),
}

_ALIAS_PENALTIES: dict[str, tuple[str, ...]] = {
    "lightweight": ("large", "70b", "72b", "reason"),
    "coding": ("vision", "image"),
    "heavyweight": ("mini", "nano", "small"),
}


class RouterServiceError(Exception):
    def __init__(self, status_code: int, detail: Any):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class RouteCandidate:
    provider_name: str
    backend_model: str
    total_score: float
    score_breakdown: dict[str, Any]
    is_fallback: bool = False


@dataclass(frozen=True)
class StreamPlan:
    body: Iterator[str]
    headers: dict[str, str]


class RouterService:
    def __init__(self, config: RouterConfig, *, providers: dict[str, ChatProvider] | None = None, state_store: StateStore | None = None):
        self.config = config
        self.state_store = state_store or SqliteStateStore(config.db_path, rolling_window_seconds=config.rolling_window_seconds)
        self.providers = providers if providers is not None else self._build_providers()
        self._provider_names = tuple(sorted(self.providers.keys()))
        self._inventory = self._load_persisted_inventory()
        self._inventory_loaded_at = 0.0
        self._last_refresh_reason = "persisted"
        self._last_refresh_at = 0.0
        self._last_refresh_error: dict[str, Any] | None = None
        self._last_bucket_model: str | None = None
        self._last_ranking_at = 0.0
        self._last_ranking_error: dict[str, Any] | None = None
        self._last_ranking_worker: dict[str, str] | None = None

    def _build_providers(self) -> dict[str, ChatProvider]:
        providers: dict[str, ChatProvider] = {}
        if self.config.openrouter_api_key:
            providers["openrouter"] = OpenRouterProvider(
                self.config.openrouter_api_key,
                base_url=self.config.openrouter_base_url,
                http_referer=self.config.openrouter_http_referer,
                title=self.config.openrouter_title,
                default_timeout=self.config.default_timeout,
            )
        if self.config.opencode_api_key:
            providers["opencode-zen"] = OpencodeZenProvider(
                self.config.opencode_api_key,
                base_url=self.config.opencode_base_url,
                default_timeout=self.config.default_timeout,
            )
        return providers

    def _load_persisted_inventory(self) -> list[ProviderModel]:
        models: list[ProviderModel] = []
        for provider_name in self.providers:
            models.extend(self.state_store.load_inventory(provider_name))
        return models

    def readiness(self) -> ReadinessResponse:
        if not self.providers:
            return ReadinessResponse(ok=False, providers=[], detail="No providers configured.")
        detail = "Router is ready."
        if not self._inventory:
            detail = "Router is ready but inventory is not loaded yet."
        return ReadinessResponse(ok=True, providers=sorted(self.providers.keys()), detail=detail)

    def list_models(self) -> ModelsResponse:
        alias_cards: list[ModelCard] = []
        for alias in self.config.aliases:
            candidates = self.preview_routes(alias.name)
            alias_cards.append(
                ModelCard(
                    id=alias.name,
                    metadata={
                        "description": alias.description,
                        "candidate_count": len(candidates),
                        "candidates": candidates,
                    },
                )
            )
        return ModelsResponse(data=alias_cards)

    def chat_completions(self, request: ChatCompletionRequest, *, session_id: str | None = None) -> tuple[dict[str, Any], dict[str, str]]:
        active_session_id, request_for_routing = self._prepare_chat_request(request, session_id=session_id)
        payload, headers = self._execute_chat_completion(request_for_routing)
        self.state_store.save_chat_session(active_session_id, self._chat_session_messages(request_for_routing, payload))
        headers["X-Hermes-Session-Id"] = active_session_id
        return payload, headers

    def stream_chat_completions(self, request: ChatCompletionRequest, *, session_id: str | None = None) -> StreamPlan:
        active_session_id, request_for_routing = self._prepare_chat_request(request, session_id=session_id)
        candidates = self._resolve_candidates(request_for_routing.model)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request_for_routing.model}'."})

        request_payload = request_for_routing.model_dump(mode="json", exclude_none=True)
        request_payload.pop("timeout", None)
        attempt_errors: list[dict[str, Any]] = []
        selected: tuple[RouteCandidate, ProviderChatStreamResult, str | None, Iterator[str]] | None = None
        for index, candidate in enumerate(candidates):
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                continue
            try:
                stream_result = provider.chat_completions_stream(
                    candidate.backend_model,
                    request_payload,
                    timeout=request_for_routing.timeout or self.config.default_timeout,
                )
                chunk_iter = iter(stream_result.chunks)
                first_chunk: str | None = None
                try:
                    first_chunk = next(chunk_iter)
                except StopIteration:
                    first_chunk = None
                selected = (candidate, stream_result, first_chunk, chunk_iter)
                break
            except NormalizedProviderError as exc:
                self._record_failure(candidate, request_for_routing.model, exc, latency_ms=None, is_fallback=(index > 0))
                attempt_errors.append(
                    {
                        "provider": exc.provider,
                        "backend_model": exc.backend_model,
                        "category": exc.category,
                        "retryable": exc.retryable,
                        "details": exc.details,
                    }
                )
                if exc.category == "model_missing":
                    self.refresh_inventory(reason="model_missing")
                if not exc.retryable:
                    continue
        if selected is None:
            raise RouterServiceError(503, {"message": f"All route candidates failed for alias '{request.model}'.", "attempts": attempt_errors})

        candidate, stream_result, first_chunk, chunk_iter = selected
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        created = int(time.time())
        headers = {
            "Cache-Control": "no-cache",
            "X-Ghostship-Router-Backend-Provider": stream_result.provider,
            "X-Ghostship-Router-Backend-Model": stream_result.backend_model,
            "X-Hermes-Session-Id": active_session_id,
        }
        if stream_result.state.first_text_latency_ms is not None:
            headers["X-Ghostship-Router-First-Text-Latency-Ms"] = str(stream_result.state.first_text_latency_ms)

        def stream_body() -> Iterator[str]:
            role_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request_for_routing.model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(role_chunk)}\n\n"
            started_at = time.monotonic()
            emitted_parts: list[str] = []
            try:
                if first_chunk:
                    emitted_parts.append(first_chunk)
                    yield self._stream_content_chunk(completion_id, created, request_for_routing.model, first_chunk)
                for chunk in chunk_iter:
                    if not chunk:
                        continue
                    emitted_parts.append(chunk)
                    yield self._stream_content_chunk(completion_id, created, request_for_routing.model, chunk)
            except NormalizedProviderError as exc:
                self._record_failure(candidate, request_for_routing.model, exc, latency_ms=round((time.monotonic() - started_at) * 1000, 2), is_fallback=candidate.is_fallback)
                raise
            latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            first_text_latency_ms = stream_result.state.first_text_latency_ms or latency_ms
            final_payload = stream_result.state.final_payload or self._chat_payload_from_text(
                request_for_routing.model,
                stream_result.backend_model,
                "".join(emitted_parts),
                stream_result.state.usage,
            )
            self.state_store.apply_success(
                candidate.provider_name,
                candidate.backend_model,
                latency_ms=latency_ms,
                first_text_latency_ms=first_text_latency_ms,
            )
            self._apply_provider_health_guards(candidate.provider_name)
            self.state_store.record_attempt(
                RouteEvent(
                    alias=request_for_routing.model,
                    provider_name=candidate.provider_name,
                    backend_model=candidate.backend_model,
                    success=True,
                    retryable=False,
                    is_fallback=candidate.is_fallback,
                    category=None,
                    latency_ms=latency_ms,
                    first_text_latency_ms=first_text_latency_ms,
                    details={"score_breakdown": candidate.score_breakdown},
                    created_at=time.time(),
                )
            )
            self.state_store.save_chat_session(active_session_id, self._chat_session_messages(request_for_routing, final_payload))
            finish_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request_for_routing.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": self._chat_usage(final_payload),
            }
            yield f"data: {json.dumps(finish_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamPlan(body=stream_body(), headers=headers)

    def responses_create(self, request: ResponsesRequest) -> tuple[dict[str, Any], dict[str, str]]:
        if request.conversation and request.previous_response_id:
            raise RouterServiceError(400, {"message": "Cannot use both 'conversation' and 'previous_response_id'."})
        previous_response_id = request.previous_response_id
        if request.conversation:
            previous_response_id = self.state_store.get_conversation_response(request.conversation)

        input_messages = self._responses_input_messages(request.input)
        if not input_messages:
            raise RouterServiceError(400, {"message": "No user message found in input."})
        history: list[dict[str, Any]] = []
        instructions = request.instructions
        if previous_response_id:
            stored = self.state_store.get_response(previous_response_id)
            if stored is None:
                raise RouterServiceError(404, {"message": f"Previous response not found: {previous_response_id}"})
            history = list(stored.get("conversation_history", []))
            if instructions is None:
                instructions = stored.get("instructions")
        history.extend(input_messages[:-1])
        if request.truncation == "auto" and len(history) > 100:
            history = history[-100:]
        chat_messages: list[dict[str, Any]] = []
        if instructions:
            chat_messages.append({"role": "system", "content": instructions})
        chat_messages.extend(history)
        chat_messages.append(input_messages[-1])
        chat_request = ChatCompletionRequest.model_validate(
            {
                "model": request.model,
                "messages": chat_messages,
                "temperature": request.model_extra.get("temperature") if request.model_extra else None,
                "max_tokens": request.model_extra.get("max_output_tokens") if request.model_extra else None,
                "timeout": request.timeout,
            }
        )
        payload, headers = self._execute_chat_completion(chat_request)
        response_id = f"resp_{uuid.uuid4().hex[:28]}"
        response_payload = self._responses_payload(response_id, request.model, payload)
        conversation_history = [message for message in chat_messages if message.get("role") != "system"]
        conversation_history.append({"role": "assistant", "content": self._assistant_text_from_payload(payload)})
        if request.store:
            self.state_store.put_response(response_id, response_payload, conversation_history=conversation_history, instructions=instructions)
            if request.conversation:
                self.state_store.set_conversation_response(request.conversation, response_id)
        headers["X-Hermes-Session-Id"] = headers.get("X-Hermes-Session-Id", str(uuid.uuid4()))
        return response_payload, headers

    def get_response(self, response_id: str) -> dict[str, Any]:
        stored = self.state_store.get_response(response_id)
        if stored is None:
            raise RouterServiceError(404, {"message": f"Response not found: {response_id}"})
        return stored["response"]

    def delete_response(self, response_id: str) -> dict[str, Any]:
        deleted = self.state_store.delete_response(response_id)
        if not deleted:
            raise RouterServiceError(404, {"message": f"Response not found: {response_id}"})
        return {"id": response_id, "object": "response", "deleted": True}

    def _execute_chat_completion(self, request: ChatCompletionRequest) -> tuple[dict[str, Any], dict[str, str]]:
        candidates = self._resolve_candidates(request.model)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request.model}'."})
        request_payload = request.model_dump(mode="json", exclude_none=True)
        request_payload.pop("timeout", None)
        errors: list[dict[str, Any]] = []
        for index, candidate in enumerate(candidates):
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                continue
            start = time.monotonic()
            try:
                result = provider.chat_completions(candidate.backend_model, request_payload, timeout=request.timeout or self.config.default_timeout)
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                first_text_latency_ms = result.first_text_latency_ms or latency_ms
                self.state_store.apply_success(candidate.provider_name, candidate.backend_model, latency_ms=latency_ms, first_text_latency_ms=first_text_latency_ms)
                self._apply_provider_health_guards(candidate.provider_name)
                self.state_store.record_attempt(
                    RouteEvent(
                        alias=request.model,
                        provider_name=candidate.provider_name,
                        backend_model=candidate.backend_model,
                        success=True,
                        retryable=False,
                        is_fallback=(index > 0),
                        category=None,
                        latency_ms=latency_ms,
                        first_text_latency_ms=first_text_latency_ms,
                        details={"result_provider": result.provider, "score_breakdown": candidate.score_breakdown},
                        created_at=time.time(),
                    )
                )
                headers = {
                    "X-Ghostship-Router-Backend-Provider": result.provider,
                    "X-Ghostship-Router-Backend-Model": result.backend_model,
                    "X-Ghostship-Router-Latency-Ms": str(latency_ms),
                    "X-Ghostship-Router-First-Text-Latency-Ms": str(first_text_latency_ms),
                }
                return result.payload, headers
            except NormalizedProviderError as exc:
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                self._record_failure(candidate, request.model, exc, latency_ms=latency_ms, is_fallback=(index > 0))
                errors.append(
                    {
                        "provider": exc.provider,
                        "backend_model": exc.backend_model,
                        "category": exc.category,
                        "retryable": exc.retryable,
                        "details": exc.details,
                    }
                )
                if exc.category == "model_missing":
                    self.refresh_inventory(reason="model_missing")
                if not exc.retryable:
                    continue
        raise RouterServiceError(503, {"message": f"All route candidates failed for alias '{request.model}'.", "attempts": errors})

    def _prepare_chat_request(self, request: ChatCompletionRequest, *, session_id: str | None) -> tuple[str, ChatCompletionRequest]:
        active_session_id = session_id or str(uuid.uuid4())
        if not session_id:
            return active_session_id, request
        stored_messages = self.state_store.load_chat_session(session_id)
        if not stored_messages:
            return active_session_id, request
        request_messages = request.model_dump(mode="json", exclude_none=True)["messages"]
        system_messages = [message for message in request_messages if message.get("role") == "system"]
        non_system = [message for message in request_messages if message.get("role") != "system"]
        if non_system:
            merged = [*system_messages, *stored_messages, non_system[-1]]
        else:
            merged = [*system_messages, *stored_messages]
        return active_session_id, ChatCompletionRequest.model_validate({**request.model_dump(mode="json", exclude_none=True), "messages": merged})

    def _chat_session_messages(self, request: ChatCompletionRequest, payload: dict[str, Any]) -> list[dict[str, Any]]:
        messages = [message.model_dump(mode="json", exclude_none=True) for message in request.messages if message.role != "system"]
        messages.append({"role": "assistant", "content": self._assistant_text_from_payload(payload)})
        return messages

    def _assistant_text_from_payload(self, payload: dict[str, Any]) -> str:
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [str(item.get("text", "")) for item in content if isinstance(item, dict)]
            return "\n".join(part for part in parts if part)
        return str(content or "")

    def _chat_payload_from_text(
        self,
        model_alias: str,
        backend_model: str,
        text: str,
        usage: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": backend_model or model_alias,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": usage,
        }

    def _chat_usage(self, payload: dict[str, Any]) -> dict[str, int]:
        usage = payload.get("usage") or {}
        return {
            "prompt_tokens": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }

    def _stream_content_chunk(self, completion_id: str, created: int, model: str, chunk: str) -> str:
        payload = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
        }
        return f"data: {json.dumps(payload)}\n\n"

    def _record_failure(
        self,
        candidate: RouteCandidate,
        alias: str,
        exc: NormalizedProviderError,
        *,
        latency_ms: float | None,
        is_fallback: bool,
    ) -> None:
        logger.warning(
            "router candidate failed: provider=%s backend_model=%s category=%s retryable=%s",
            exc.provider,
            exc.backend_model,
            exc.category,
            exc.retryable,
        )
        self.state_store.apply_failure(candidate.provider_name, candidate.backend_model, category=exc.category, retryable=exc.retryable)
        self._apply_provider_health_guards(candidate.provider_name)
        self.state_store.record_attempt(
            RouteEvent(
                alias=alias,
                provider_name=candidate.provider_name,
                backend_model=candidate.backend_model,
                success=False,
                retryable=exc.retryable,
                is_fallback=is_fallback,
                category=exc.category,
                latency_ms=latency_ms,
                first_text_latency_ms=None,
                details={"provider_error": exc.details, "score_breakdown": candidate.score_breakdown},
                created_at=time.time(),
            )
        )

    def _responses_input_messages(self, raw_input: Any) -> list[dict[str, Any]]:
        if isinstance(raw_input, str):
            return [{"role": "user", "content": raw_input}]
        if not isinstance(raw_input, list):
            raise RouterServiceError(400, {"message": "'input' must be a string or array."})
        messages: list[dict[str, Any]] = []
        for item in raw_input:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
                continue
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "user"))
            content = item.get("content", "")
            if isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, str):
                        parts.append(part)
                    elif isinstance(part, dict):
                        text = part.get("text")
                        if isinstance(text, str):
                            parts.append(text)
                content = "\n".join(part for part in parts if part)
            messages.append({"role": role, "content": content})
        return messages

    def _responses_payload(self, response_id: str, model: str, chat_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": response_id,
            "object": "response",
            "status": "completed",
            "created_at": int(time.time()),
            "model": model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": self._assistant_text_from_payload(chat_payload)}],
                }
            ],
            "usage": {
                "input_tokens": int((chat_payload.get("usage") or {}).get("prompt_tokens") or (chat_payload.get("usage") or {}).get("input_tokens") or 0),
                "output_tokens": int((chat_payload.get("usage") or {}).get("completion_tokens") or (chat_payload.get("usage") or {}).get("output_tokens") or 0),
                "total_tokens": int((chat_payload.get("usage") or {}).get("total_tokens") or 0),
            },
        }

    def refresh_inventory(self, *, reason: str) -> list[ProviderModel]:
        refreshed: list[ProviderModel] = []
        errors: dict[str, Any] = {}
        for provider_name, provider in self.providers.items():
            try:
                models = provider.list_models(timeout=self.config.default_timeout)
                refreshed.extend(models)
                self.state_store.save_inventory(provider_name, models, reason=reason)
                self.state_store.record_refresh(provider_name, reason=reason, success=True, model_count=len(models))
            except NormalizedProviderError as exc:
                errors[provider_name] = {"category": exc.category, "details": exc.details}
                self.state_store.record_refresh(
                    provider_name,
                    reason=reason,
                    success=False,
                    category=exc.category,
                    details=exc.details,
                )
                self._apply_provider_health_guards(provider_name)
        self._inventory = []
        for provider_name in self.providers:
            self._inventory.extend(self.state_store.load_inventory(provider_name))
        self._inventory_loaded_at = time.time()
        self._last_refresh_reason = reason
        self._last_refresh_at = self._inventory_loaded_at
        self._last_refresh_error = errors or None
        if self.config.ranking_enabled and self._ranking_due():
            self._refresh_rankings(self._inventory)
        if errors:
            self._log_event("refresh_partial", reason=reason, model_count=len(self._inventory), errors=errors)
        else:
            self._log_event("refresh_complete", reason=reason, model_count=len(self._inventory))
        return self._inventory

    def debug_state(self) -> dict[str, Any]:
        return {
            "providers": list(self._provider_names),
            "last_refresh_reason": self._last_refresh_reason,
            "last_refresh_at": self._last_refresh_at,
            "last_refresh_error": self._last_refresh_error,
            "last_ranking_at": self._last_ranking_at,
            "last_ranking_error": self._last_ranking_error,
            "last_ranking_worker": self._last_ranking_worker,
            "assisted_bucket_model": self._last_bucket_model,
            "inventory_ttl_seconds": self.config.inventory_ttl_seconds,
            "refresh_interval_seconds": self.config.refresh_interval_seconds,
            "ranking_interval_seconds": self.config.ranking_interval_seconds,
            "state": self.state_store.snapshot(),
        }

    def debug_events(self) -> list[dict[str, Any]]:
        return self.state_store.get_recent_events(self.config.debug_event_limit)

    def debug_providers(self) -> list[dict[str, Any]]:
        provider_state = self.state_store.get_provider_state()
        overrides = self._effective_overrides()
        details: list[dict[str, Any]] = []
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            override = overrides["provider_map"].get(provider_name, {})
            details.append(
                {
                    "provider_name": provider_name,
                    "enabled": self._provider_enabled(provider_name, overrides=overrides),
                    "cooldown_until": state.get("cooldown_until", 0),
                    "recent_failure": state.get("recent_failure", 0),
                    "recent_rate_limit": state.get("recent_rate_limit", 0),
                    "recent_timeout": state.get("recent_timeout", 0),
                    "recent_auth_failure": state.get("recent_auth_failure", 0),
                    "recent_exhaustion": state.get("recent_exhaustion", 0),
                    "weight": self._provider_weight(provider_name, overrides=overrides),
                    "override": override or None,
                    "state": state,
                }
            )
        return details

    def debug_rankings(self, alias: str) -> dict[str, Any]:
        alias_config = self.config.alias_map().get(alias)
        if alias_config is None:
            raise RouterServiceError(404, {"message": f"Unknown logical model alias '{alias}'."})
        candidates: list[dict[str, Any]] = []
        for model in self._inventory_for_all():
            if not self._model_effectively_enabled(model.provider, model.id):
                continue
            breakdown = self._score_breakdown(alias, model)
            candidates.append(
                {
                    "provider_name": model.provider,
                    "backend_model": model.id,
                    "is_free": model.is_free,
                    **breakdown,
                }
            )
        ordered = sorted(candidates, key=lambda item: item["total_score"], reverse=True)
        return {"alias": alias, "candidates": ordered[: self.config.alias_model_limit * 4]}

    def debug_model(self, provider_name: str, backend_model: str) -> dict[str, Any]:
        model = self._lookup_model(provider_name, backend_model)
        if model is None:
            raise RouterServiceError(404, {"message": f"Unknown backend model '{provider_name}/{backend_model}'."})
        return {
            "provider_name": provider_name,
            "backend_model": backend_model,
            "inventory": {
                "is_free": model.is_free,
                "tags": model.tags,
                "metadata": model.metadata,
            },
            "model_state": self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {}),
            "provider_state": self.state_store.get_provider_state().get(provider_name, {}),
            "ranking": self.state_store.get_rankings().get(self._model_key(provider_name, backend_model), {}),
            "overrides": self._model_override_payload(provider_name, backend_model),
        }

    def metrics_text(self) -> str:
        route_rows = self.state_store.get_route_metric_rows()
        refresh_rows = self.state_store.get_refresh_metric_rows()
        model_state = self.state_store.get_model_state()
        provider_state = self.state_store.get_provider_state()
        rankings = self.state_store.get_rankings()
        lines = [
            "# HELP ghostship_router_requests_total Total router request attempts by alias, provider, model, and result.",
            "# TYPE ghostship_router_requests_total counter",
        ]
        for row in route_rows:
            lines.append(
                self._prom_metric(
                    "ghostship_router_requests_total",
                    row["count"],
                    alias=row["alias"],
                    provider=row["provider_name"],
                    backend_model=row["backend_model"],
                    result=("success" if row["success"] else "failure"),
                    category=(row["category"] or "none"),
                    retryable=("true" if row["retryable"] else "false"),
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_failovers_total Total attempts that used a non-primary candidate.",
                "# TYPE ghostship_router_failovers_total counter",
            ]
        )
        failover_total = sum(int(row["count"]) for row in route_rows if row["is_fallback"])
        lines.append(f"ghostship_router_failovers_total {failover_total}")
        lines.extend(
            [
                "# HELP ghostship_router_refresh_total Total provider refresh outcomes by provider and reason.",
                "# TYPE ghostship_router_refresh_total counter",
            ]
        )
        for row in refresh_rows:
            lines.append(
                self._prom_metric(
                    "ghostship_router_refresh_total",
                    row["count"],
                    provider=row["provider_name"],
                    reason=row["reason"],
                    result=("success" if row["success"] else "failure"),
                    category=(row["category"] or "none"),
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_provider_cooldown_active Whether a provider is currently suppressed.",
                "# TYPE ghostship_router_provider_cooldown_active gauge",
            ]
        )
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            lines.append(
                self._prom_metric(
                    "ghostship_router_provider_cooldown_active",
                    1 if self._provider_is_cooling_down(provider_name, state=state) else 0,
                    provider=provider_name,
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_model_cooldown_active Whether a backend model is currently cooling down.",
                "# TYPE ghostship_router_model_cooldown_active gauge",
            ]
        )
        for key, state in model_state.items():
            provider_name, backend_model = key.split("::", 1)
            lines.append(
                self._prom_metric(
                    "ghostship_router_model_cooldown_active",
                    1 if self._is_cooling_down(provider_name, backend_model, state=state) else 0,
                    provider=provider_name,
                    backend_model=backend_model,
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_model_latency_avg_ms Rolling average total latency for backend models.",
                "# TYPE ghostship_router_model_latency_avg_ms gauge",
            ]
        )
        for key, state in model_state.items():
            provider_name, backend_model = key.split("::", 1)
            value = state.get("latency_avg_ms")
            if value is not None:
                lines.append(self._prom_metric("ghostship_router_model_latency_avg_ms", value, provider=provider_name, backend_model=backend_model))
        lines.extend(
            [
                "# HELP ghostship_router_model_first_text_latency_avg_ms Rolling average first-text latency for backend models.",
                "# TYPE ghostship_router_model_first_text_latency_avg_ms gauge",
            ]
        )
        for key, state in model_state.items():
            provider_name, backend_model = key.split("::", 1)
            value = state.get("first_text_latency_avg_ms")
            if value is not None:
                lines.append(self._prom_metric("ghostship_router_model_first_text_latency_avg_ms", value, provider=provider_name, backend_model=backend_model))
        lines.extend(
            [
                "# HELP ghostship_router_candidate_count Current routable candidate count by alias.",
                "# TYPE ghostship_router_candidate_count gauge",
            ]
        )
        for alias in self.config.alias_map():
            lines.append(self._prom_metric("ghostship_router_candidate_count", len(self.preview_routes(alias)), alias=alias))
        lines.extend(
            [
                "# HELP ghostship_router_model_score Current total routing score by alias and backend model.",
                "# TYPE ghostship_router_model_score gauge",
            ]
        )
        for alias in self.config.alias_map():
            for model in self._inventory_for_all():
                if not self._model_effectively_enabled(model.provider, model.id):
                    continue
                breakdown = self._score_breakdown(alias, model)
                lines.append(
                    self._prom_metric(
                        "ghostship_router_model_score",
                        breakdown["total_score"],
                        alias=alias,
                        provider=model.provider,
                        backend_model=model.id,
                    )
                )
        lines.extend(
            [
                "# HELP ghostship_router_model_ranking_confidence Current ranking confidence by backend model.",
                "# TYPE ghostship_router_model_ranking_confidence gauge",
            ]
        )
        for key, ranking in rankings.items():
            provider_name, backend_model = key.split("::", 1)
            lines.append(
                self._prom_metric(
                    "ghostship_router_model_ranking_confidence",
                    ranking.get("confidence") or 0,
                    provider=provider_name,
                    backend_model=backend_model,
                )
            )
        return "\n".join(lines) + "\n"

    def preview_routes(self, alias: str) -> list[dict[str, Any]]:
        try:
            candidates = self._resolve_candidates(alias)
        except RouterServiceError:
            return []
        return [
            {
                "provider_name": candidate.provider_name,
                "backend_model": candidate.backend_model,
                "is_free": self._model_is_free(candidate.provider_name, candidate.backend_model),
                "is_fallback": candidate.is_fallback,
                **candidate.score_breakdown,
            }
            for candidate in candidates
        ]

    def _resolve_candidates(self, alias: str) -> list[RouteCandidate]:
        alias_config = self.config.alias_map().get(alias)
        if alias_config is None:
            direct_candidates = self._resolve_direct_model(alias)
            if direct_candidates:
                return direct_candidates
            raise RouterServiceError(404, {"message": f"Unknown logical model alias '{alias}'."})

        pinned_models = self._alias_pins(alias, alias_config)
        candidates = self._preferred_candidates(pinned_models)
        if not candidates:
            discovered = self._discover_alias_candidates(alias_config)
            candidates = [
                RouteCandidate(
                    provider_name=model.provider,
                    backend_model=model.id,
                    total_score=self._score_breakdown(alias, model)["total_score"],
                    score_breakdown=self._score_breakdown(alias, model),
                )
                for model in discovered
            ]
        return [RouteCandidate(**{**candidate.__dict__, "is_fallback": index > 0}) for index, candidate in enumerate(candidates)]

    def _resolve_direct_model(self, model_name: str) -> list[RouteCandidate]:
        if not self.config.allow_direct_models:
            return []
        return self._preferred_candidates((model_name,))

    def _preferred_candidates(self, model_ids: tuple[str, ...], *, inventory: list[ProviderModel] | None = None) -> list[RouteCandidate]:
        candidates: list[RouteCandidate] = []
        known_inventory = inventory if inventory is not None else self._inventory_for_all()
        for model_id in model_ids:
            normalized = model_id.removeprefix("opencode/")
            matched = [model for model in known_inventory if model.id == normalized or model.id == model_id]
            if not matched and normalized == model_id and "openrouter" in self.providers:
                matched.append(ProviderModel(id=model_id, provider="openrouter", is_free=model_id.endswith(":free")))
            for model in matched:
                if not self._model_effectively_enabled(model.provider, model.id):
                    continue
                if self._provider_is_cooling_down(model.provider):
                    continue
                if self._is_cooling_down(model.provider, model.id):
                    continue
                breakdown = self._score_breakdown(self._alias_for_model_id(model_id) or "coding", model)
                candidate = RouteCandidate(
                    provider_name=model.provider,
                    backend_model=model.id,
                    total_score=breakdown["total_score"],
                    score_breakdown=breakdown,
                )
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _discover_alias_candidates(self, alias: AliasConfig) -> list[ProviderModel]:
        filtered = [
            model
            for model in self._inventory_for_all()
            if self._model_effectively_enabled(model.provider, model.id)
            and not self._is_cooling_down(model.provider, model.id)
            and not self._provider_is_cooling_down(model.provider)
        ]
        scored = sorted(filtered, key=lambda model: self._score_breakdown(alias.name, model)["total_score"], reverse=True)
        return [model for model in scored if self._score_breakdown(alias.name, model)["total_score"] > 0][: self.config.alias_model_limit]

    def _inventory_for_all(self) -> list[ProviderModel]:
        if not self._inventory:
            self.refresh_inventory(reason="lazy")
        return list(self._inventory)

    def _score_breakdown(self, alias: str, model: ProviderModel) -> dict[str, Any]:
        model_state = self.state_store.get_model_state().get(self._model_key(model.provider, model.id), {})
        provider_state = self.state_store.get_provider_state().get(model.provider, {})
        ranking = self.state_store.get_rankings().get(self._model_key(model.provider, model.id), {})
        overrides = self._effective_overrides()
        lowered = model.id.lower()
        hint_score = 0.0
        penalty_score = 0.0
        for token in _ALIAS_HINTS.get(alias, ()):
            if token in lowered:
                hint_score += 4.0
        for token in model.tags:
            if token == alias:
                hint_score += 3.0
        for token in _ALIAS_PENALTIES.get(alias, ()):
            if token in lowered:
                penalty_score -= 3.0
        free_score = 100.0 if model.is_free else 0.0
        provider_bias = 2.0 if model.provider == "openrouter" else 0.0
        model_health = (
            float(model_state.get("recent_success", 0)) * 2.0
            - float(model_state.get("recent_failure", 0)) * 3.0
            - float(model_state.get("recent_rate_limit", 0)) * 4.0
            - float(model_state.get("recent_timeout", 0)) * 3.0
            - float(model_state.get("recent_auth_failure", 0)) * 12.0
            - float(model_state.get("recent_exhaustion", 0)) * 5.0
        )
        provider_health = (
            float(provider_state.get("recent_success", 0))
            - float(provider_state.get("recent_failure", 0)) * 2.0
            - float(provider_state.get("recent_rate_limit", 0)) * 3.0
            - float(provider_state.get("recent_timeout", 0)) * 2.0
            - float(provider_state.get("recent_auth_failure", 0)) * 10.0
            - float(provider_state.get("recent_exhaustion", 0)) * 4.0
        )
        latency_penalty = -((float(model_state.get("first_text_latency_avg_ms") or model_state.get("latency_avg_ms") or 0.0)) / 1000.0)
        alias_scores = ranking.get("alias_scores", {})
        rerank_scores = ranking.get("rerank_scores", {})
        learned_score = float(alias_scores.get(alias, 0.0)) + float(rerank_scores.get(alias, 0.0))
        provider_weight = self._provider_weight(model.provider, overrides=overrides)
        model_weight = self._model_weight(model.provider, model.id, overrides=overrides)
        cooldown_penalty = -1000.0 if self._is_cooling_down(model.provider, model.id, state=model_state) else 0.0
        provider_cooldown_penalty = -500.0 if self._provider_is_cooling_down(model.provider, state=provider_state) else 0.0
        total_score = round(
            free_score
            + provider_bias
            + hint_score
            + penalty_score
            + model_health
            + provider_health
            + latency_penalty
            + learned_score
            + provider_weight
            + model_weight
            + cooldown_penalty
            + provider_cooldown_penalty,
            3,
        )
        return {
            "total_score": total_score,
            "free_score": free_score,
            "provider_bias": provider_bias,
            "hint_score": hint_score,
            "penalty_score": penalty_score,
            "model_health_score": round(model_health, 3),
            "provider_health_score": round(provider_health, 3),
            "latency_penalty": round(latency_penalty, 3),
            "learned_ranking_score": round(learned_score, 3),
            "provider_weight": provider_weight,
            "model_weight": model_weight,
            "cooldown_penalty": cooldown_penalty,
            "provider_cooldown_penalty": provider_cooldown_penalty,
            "ranking_reason": ranking.get("reason"),
            "ranking_confidence": ranking.get("confidence"),
            "cooldown_until": model_state.get("cooldown_until", 0),
            "provider_cooldown_until": provider_state.get("cooldown_until", 0),
            "last_latency_ms": model_state.get("last_latency_ms"),
            "last_first_text_latency_ms": model_state.get("last_first_text_latency_ms"),
        }

    def _model_allowed(self, model_id: str) -> bool:
        normalized = model_id.removeprefix("opencode/")
        if self.config.allow_models and normalized not in self.config.allow_models and model_id not in self.config.allow_models:
            return False
        if normalized in self.config.block_models or model_id in self.config.block_models:
            return False
        if normalized in self.config.disabled_models or model_id in self.config.disabled_models:
            return False
        return True

    def _model_effectively_enabled(self, provider_name: str, backend_model: str) -> bool:
        overrides = self._effective_overrides()
        model_override = overrides["model_map"].get(self._model_key(provider_name, backend_model))
        if model_override and model_override.get("enabled") is False:
            return False
        if model_override and model_override.get("enabled") is True:
            return True
        if not self._provider_enabled(provider_name, overrides=overrides):
            return False
        return self._model_allowed(backend_model)

    def _model_is_free(self, provider_name: str, backend_model: str, *, inventory: list[ProviderModel] | None = None) -> bool:
        for model in (inventory if inventory is not None else self._inventory_for_all()):
            if model.provider == provider_name and model.id == backend_model:
                return model.is_free
        return False

    def _is_cooling_down(self, provider_name: str, backend_model: str, *, state: dict[str, Any] | None = None) -> bool:
        model_state = state or self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        return float(model_state.get("cooldown_until", 0) or 0) > time.time()

    def _provider_is_cooling_down(self, provider_name: str, *, state: dict[str, Any] | None = None) -> bool:
        provider_state = state or self.state_store.get_provider_state().get(provider_name, {})
        return float(provider_state.get("cooldown_until", 0) or 0) > time.time()

    def _provider_enabled(self, provider_name: str, *, overrides: dict[str, Any] | None = None) -> bool:
        merged = overrides or self._effective_overrides()
        provider_override = merged["provider_map"].get(provider_name)
        if provider_override and provider_override.get("enabled") is False:
            return False
        if provider_override and provider_override.get("enabled") is True:
            return True
        return provider_name not in self.config.disabled_providers

    def _provider_weight(self, provider_name: str, *, overrides: dict[str, Any] | None = None) -> float:
        merged = overrides or self._effective_overrides()
        provider_override = merged["provider_map"].get(provider_name, {})
        return float(self.config.provider_weight_overrides.get(provider_name, 0.0)) + float(provider_override.get("weight", 0.0))

    def _model_weight(self, provider_name: str, backend_model: str, *, overrides: dict[str, Any] | None = None) -> float:
        merged = overrides or self._effective_overrides()
        model_override = merged["model_map"].get(self._model_key(provider_name, backend_model), {})
        config_weight = self.config.model_weight_overrides.get(self._model_key(provider_name, backend_model), self.config.model_weight_overrides.get(backend_model, 0.0))
        return float(config_weight) + float(model_override.get("weight", 0.0))

    def _effective_overrides(self) -> dict[str, Any]:
        raw = self.state_store.get_overrides()
        provider_map = {item["provider_name"]: item for item in raw.get("providers", [])}
        model_map = {self._model_key(item["provider_name"], item["backend_model"]): item for item in raw.get("models", [])}
        alias_pins = {item["alias"]: tuple(item["models"]) for item in raw.get("alias_pins", [])}
        return {
            "provider_map": provider_map,
            "model_map": model_map,
            "alias_pins": {
                alias: alias_pins.get(alias) or self.config.alias_pin_overrides.get(alias) or ()
                for alias in self.config.alias_map()
            },
        }

    def _alias_pins(self, alias: str, alias_config: AliasConfig) -> tuple[str, ...]:
        overrides = self._effective_overrides()
        if overrides["alias_pins"].get(alias):
            return tuple(overrides["alias_pins"][alias])
        return alias_config.preferred_models

    def _apply_provider_health_guards(self, provider_name: str) -> None:
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        if not provider_state:
            return
        now = time.time()
        category: str | None = None
        if float(provider_state.get("recent_auth_failure", 0)) >= 1.0:
            category = "unauthorized"
        elif float(provider_state.get("recent_exhaustion", 0)) >= self.config.provider_exhaustion_threshold:
            category = "quota_exhausted"
        elif float(provider_state.get("recent_rate_limit", 0)) >= self.config.provider_rate_limit_threshold:
            category = "rate_limited"
        elif float(provider_state.get("recent_timeout", 0)) >= self.config.provider_timeout_threshold:
            category = "timeout"
        elif float(provider_state.get("recent_failure", 0)) >= self.config.provider_failure_threshold:
            category = "server_error"
        if category is None:
            return
        self.state_store.set_provider_cooldown(
            provider_name,
            cooldown_until=now + self.config.provider_cooldown_seconds,
            category=category,
            details={"source": "provider_guard"},
        )

    def _ranking_due(self) -> bool:
        if not self.config.ranking_enabled:
            return False
        if self._last_ranking_at == 0:
            return True
        return (time.time() - self._last_ranking_at) >= self.config.ranking_interval_seconds

    def _refresh_rankings(self, models: list[ProviderModel]) -> None:
        worker = self._select_ranking_worker(models)
        if worker is None:
            self._last_ranking_error = {"message": "No healthy free lightweight ranking worker available."}
            self._last_ranking_worker = None
            self._last_bucket_model = None
            return
        provider = self.providers.get(worker.provider_name)
        if provider is None:
            return
        try:
            classifications, rankings = self._rank_inventory_with_worker(provider, worker.backend_model, models)
        except NormalizedProviderError as exc:
            self._last_ranking_error = {"category": exc.category, "details": exc.details}
            self._last_ranking_worker = {"provider_name": worker.provider_name, "backend_model": worker.backend_model}
            self._last_bucket_model = None
            self._log_event("ranking_failed", provider=worker.provider_name, backend_model=worker.backend_model, category=exc.category)
            return
        if classifications:
            self.state_store.save_classifications(classifications, source=worker.backend_model)
        if rankings:
            self.state_store.save_rankings(
                rankings,
                source="lightweight-free-worker",
                worker_provider_name=worker.provider_name,
                worker_backend_model=worker.backend_model,
            )
        self._last_ranking_at = time.time()
        self._last_ranking_error = None
        self._last_ranking_worker = {"provider_name": worker.provider_name, "backend_model": worker.backend_model}
        self._last_bucket_model = worker.backend_model
        self._inventory = []
        for provider_name in self.providers:
            self._inventory.extend(self.state_store.load_inventory(provider_name))
        self._log_event("ranking_complete", worker_provider=worker.provider_name, worker_backend_model=worker.backend_model, ranked_models=len(rankings))

    def _select_ranking_worker(self, models: list[ProviderModel]) -> RouteCandidate | None:
        override_model = self.config.ranking_worker_model or self.config.assisted_bucket_model
        if override_model:
            forced = self._preferred_candidates((override_model,), inventory=models)
            if forced:
                first = forced[0]
                if self._model_is_free(first.provider_name, first.backend_model, inventory=models):
                    return first
        lightweight = self.config.alias_map().get("lightweight")
        if lightweight is None:
            return None
        candidates = []
        for model in models:
            if not model.is_free:
                continue
            if not self._model_effectively_enabled(model.provider, model.id):
                continue
            if self._provider_is_cooling_down(model.provider):
                continue
            if self._is_cooling_down(model.provider, model.id):
                continue
            breakdown = self._score_breakdown("lightweight", model)
            if breakdown["total_score"] <= 0:
                continue
            candidates.append(
                RouteCandidate(
                    provider_name=model.provider,
                    backend_model=model.id,
                    total_score=breakdown["total_score"],
                    score_breakdown=breakdown,
                )
            )
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item.total_score, reverse=True)[0]

    def _rank_inventory_with_worker(
        self,
        provider: ChatProvider,
        worker_backend_model: str,
        models: list[ProviderModel],
    ) -> tuple[dict[str, tuple[str, ...]], dict[str, dict[str, Any]]]:
        classifications: dict[str, tuple[str, ...]] = {}
        rankings: dict[str, dict[str, Any]] = {}
        batches = [models[index : index + self.config.assisted_bucket_batch_size] for index in range(0, len(models), self.config.assisted_bucket_batch_size)]
        for batch in batches:
            prompt = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You classify router backend models. "
                            "Return strict JSON with the shape "
                            "{\"models\": [{\"provider\": \"...\", \"id\": \"...\", \"tags\": [\"lightweight\"], "
                            "\"alias_scores\": {\"lightweight\": 0-12, \"coding\": 0-12, \"heavyweight\": 0-12}, "
                            "\"reason\": \"...\", \"confidence\": 0-1}]}. "
                            "Use only the aliases lightweight, coding, heavyweight."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "models": [
                                    {
                                        "provider": model.provider,
                                        "id": model.id,
                                        "is_free": model.is_free,
                                        "tags": list(model.tags),
                                        "metadata": model.metadata,
                                    }
                                    for model in batch
                                ]
                            },
                            sort_keys=True,
                        ),
                    },
                ],
                "temperature": 0,
            }
            result = provider.chat_completions(worker_backend_model, prompt, timeout=min(self.config.default_timeout, 20.0))
            payload = self._parse_json_completion(result.payload)
            for item in payload.get("models", []):
                item_id = str(item.get("id", "")).strip()
                provider_name = str(item.get("provider", "")).strip()
                if not item_id or not provider_name:
                    continue
                key = self._model_key(provider_name, item_id)
                tags = tuple(tag for tag in item.get("tags", []) if tag in _ALIASES)
                if tags:
                    classifications[item_id] = tags
                rankings[key] = {
                    "provider_name": provider_name,
                    "backend_model": item_id,
                    "alias_scores": {
                        alias: float(item.get("alias_scores", {}).get(alias, 0.0))
                        for alias in _ALIASES
                    },
                    "rerank_scores": rankings.get(key, {}).get("rerank_scores", {}),
                    "reason": str(item.get("reason", "")).strip() or None,
                    "confidence": float(item.get("confidence", 0.0) or 0.0),
                }
        shortlist_scores = self._rerank_shortlists(provider, worker_backend_model, models)
        for key, rerank_payload in shortlist_scores.items():
            current = rankings.setdefault(
                key,
                {
                    "provider_name": key.split("::", 1)[0],
                    "backend_model": key.split("::", 1)[1],
                    "alias_scores": {alias: 0.0 for alias in _ALIASES},
                    "rerank_scores": {},
                    "reason": None,
                    "confidence": 0.0,
                },
            )
            merged = dict(current.get("rerank_scores", {}))
            merged.update(rerank_payload["rerank_scores"])
            current["rerank_scores"] = merged
            if rerank_payload.get("reason"):
                current["reason"] = rerank_payload["reason"]
        return classifications, rankings

    def _rerank_shortlists(self, provider: ChatProvider, worker_backend_model: str, models: list[ProviderModel]) -> dict[str, dict[str, Any]]:
        rerankings: dict[str, dict[str, Any]] = {}
        for alias in _ALIASES:
            shortlist = sorted(models, key=lambda model: self._score_breakdown(alias, model)["total_score"], reverse=True)[: self.config.ranking_shortlist_size]
            if not shortlist:
                continue
            prompt = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Rank backend models for a router alias. "
                            "Return strict JSON with the shape "
                            "{\"alias\": \"coding\", \"ordered\": [\"provider::model\", ...], \"reason\": \"...\"}."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "alias": alias,
                                "candidates": [
                                    {
                                        "provider": model.provider,
                                        "id": model.id,
                                        "is_free": model.is_free,
                                        "tags": list(model.tags),
                                        "metadata": model.metadata,
                                        "heuristic_score": self._score_breakdown(alias, model)["total_score"],
                                    }
                                    for model in shortlist
                                ],
                            },
                            sort_keys=True,
                        ),
                    },
                ],
                "temperature": 0,
            }
            try:
                result = provider.chat_completions(worker_backend_model, prompt, timeout=min(self.config.default_timeout, 20.0))
            except NormalizedProviderError as exc:
                self._log_event("rerank_failed", alias=alias, category=exc.category)
                continue
            payload = self._parse_json_completion(result.payload)
            ordered = [entry for entry in payload.get("ordered", []) if isinstance(entry, str)]
            for index, key in enumerate(ordered):
                bonus = float(max(len(ordered) - index, 1))
                rerankings.setdefault(key, {"rerank_scores": {}, "reason": payload.get("reason")})
                rerankings[key]["rerank_scores"][alias] = bonus
        return rerankings

    def _parse_json_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        text = str(content).strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _prom_metric(self, name: str, value: Any, **labels: str) -> str:
        rendered_labels = ",".join(f'{key}="{self._prom_escape(label)}"' for key, label in sorted(labels.items()))
        if rendered_labels:
            return f"{name}{{{rendered_labels}}} {value}"
        return f"{name} {value}"

    @staticmethod
    def _prom_escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

    def _lookup_model(self, provider_name: str, backend_model: str) -> ProviderModel | None:
        for model in self._inventory_for_all():
            if model.provider == provider_name and model.id == backend_model:
                return model
        return None

    def _model_override_payload(self, provider_name: str, backend_model: str) -> dict[str, Any]:
        overrides = self._effective_overrides()
        return {
            "provider": overrides["provider_map"].get(provider_name),
            "model": overrides["model_map"].get(self._model_key(provider_name, backend_model)),
        }

    @staticmethod
    def _model_key(provider_name: str, backend_model: str) -> str:
        return f"{provider_name}::{backend_model}"

    def _alias_for_model_id(self, model_id: str) -> str | None:
        for alias, tokens in _ALIAS_HINTS.items():
            if any(token in model_id.lower() for token in tokens):
                return alias
        return None

    def _log_event(self, event: str, **fields: Any) -> None:
        logger.info("router_event %s", json.dumps({"event": event, **fields}, sort_keys=True))
