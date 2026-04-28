from __future__ import annotations

import json
import logging
import math
import threading
import time
import uuid
from collections.abc import Iterator
from concurrent import futures
from dataclasses import dataclass
from itertools import chain
from typing import Any

from .config import AliasConfig, RouterConfig
from .models import ChatCompletionRequest, ModelCard, ModelsResponse, ReadinessResponse, ResponsesRequest
from .providers.base import ChatProvider, NormalizedProviderError, ProviderChatStreamEvent, ProviderChatStreamResult, ProviderModel
from .providers.nvidia_build import NvidiaBuildProvider
from .providers.opencode_zen import OpencodeZenProvider
from .providers.openrouter import OpenRouterProvider
from .state import RouteEvent, SqliteStateStore, StateStore

logger = logging.getLogger("hermes_router")

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

@dataclass(frozen=True)
class RouteContext:
    request_id: str
    session_id: str | None
    shape_key: str
    free_budget_seconds: float
    free_started_at: float


@dataclass(frozen=True)
class PreparedResponsesRequest:
    chat_request: ChatCompletionRequest
    instructions: str | None
    conversation_history: list[dict[str, Any]]
    previous_response_id: str | None
    request: ResponsesRequest


class RouterService:
    def __init__(self, config: RouterConfig, *, providers: dict[str, ChatProvider] | None = None, state_store: StateStore | None = None):
        self.config = config
        self.state_store = state_store or SqliteStateStore(
            config.db_path,
            rolling_window_seconds=config.rolling_window_seconds,
            exhaustion_cooldown_ladder_seconds=config.exhaustion_cooldown_ladder_seconds,
        )
        self.providers = providers if providers is not None else self._build_providers()
        self._provider_names = tuple(name for name in self.config.provider_priority if name in self.providers)
        self._inventory = self._load_persisted_inventory()
        self._inventory_loaded_at = 0.0
        self._last_refresh_reason = "persisted"
        self._last_refresh_at = 0.0
        self._last_refresh_error: dict[str, Any] | None = None
        self._refresh_lock = threading.RLock()
        self._session_affinity: dict[str, dict[str, Any]] = {}
        self._round_robin_offsets: dict[str, int] = {}
        self._deadline_executor = futures.ThreadPoolExecutor(max_workers=64, thread_name_prefix="router-provider-deadline")
        self._round_robin_deficits: dict[str, float] = {}

    def _build_providers(self) -> dict[str, ChatProvider]:
        providers: dict[str, ChatProvider] = {}
        if self.config.nvidia_build_api_key:
            providers["nvidia-build"] = NvidiaBuildProvider(
                self.config.nvidia_build_api_key,
                base_url=self.config.nvidia_build_base_url,
                default_timeout=self.config.default_timeout,
            )
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
                provider_name="opencode-zen",
                force_free_models=True,
            )
        if self.config.zenmux_api_key:
            providers["zenmux"] = OpencodeZenProvider(
                self.config.zenmux_api_key,
                base_url=self.config.zenmux_base_url,
                default_timeout=self.config.default_timeout,
                provider_name="zenmux",
                force_free_models=True,
            )
        if self.config.electron_hub_api_key:
            providers["electron-hub"] = OpencodeZenProvider(
                self.config.electron_hub_api_key,
                base_url=self.config.electron_hub_base_url,
                default_timeout=self.config.default_timeout,
                provider_name="electron-hub",
                force_free_models=True,
            )
        if self.config.opencode_go_api_key:
            providers["opencode-go"] = OpencodeZenProvider(
                self.config.opencode_go_api_key,
                base_url=self.config.opencode_go_base_url,
                default_timeout=self.config.default_timeout,
                provider_name="opencode-go",
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
        if not self._inventory:
            return ReadinessResponse(ok=False, providers=sorted(self.providers.keys()), detail="Router inventory is still loading.")
        return ReadinessResponse(ok=True, providers=sorted(self.providers.keys()), detail="Router is ready.")

    def list_models(self) -> ModelsResponse:
        self._ensure_inventory_loaded_for_request()
        alias_cards: list[ModelCard] = []
        for model in self._opencode_go_models():
            free_models = self._free_equivalent_models(model.id)
            if not free_models:
                continue
            free_providers = self._free_provider_names_for_served_model(model.id)
            candidates = self.preview_routes(model.id)
            if not candidates:
                continue
            alias_cards.append(
                ModelCard(
                    id=model.id,
                    metadata={
                        "description": self._served_model_description(model.id),
                        "free_provider_count": len(free_providers),
                        "free_providers": list(free_providers),
                        "free_provider_state": {
                            provider_name: self._provider_rpm_state(provider_name)
                            for provider_name in free_providers
                        },
                        "candidate_count": len(candidates),
                        "candidates": candidates,
                    },
                )
            )
        return ModelsResponse(data=alias_cards)

    def _free_provider_names_for_served_model(self, served_model_id: str) -> tuple[str, ...]:
        providers: list[str] = []
        for model in self._free_equivalent_models(served_model_id):
            if model.provider not in providers:
                providers.append(model.provider)
        return tuple(providers)

    def _served_model_description(self, served_model_id: str) -> str:
        alias = self.config.alias_map().get(served_model_id)
        if alias is not None and alias.description:
            return alias.description
        return f"{served_model_id} through discovered free equivalents first, then OpenCode Go."

    def chat_completions(self, request: ChatCompletionRequest, *, session_id: str | None = None) -> tuple[dict[str, Any], dict[str, str]]:
        active_session_id, request_for_routing = self._prepare_chat_request(request, session_id=session_id)
        payload, headers = self._execute_chat_completion(request_for_routing, session_id=active_session_id)
        self.state_store.save_chat_session(active_session_id, self._chat_session_messages(request_for_routing, payload))
        headers["X-Hermes-Session-Id"] = active_session_id
        return payload, headers

    def stream_chat_completions(self, request: ChatCompletionRequest, *, session_id: str | None = None) -> StreamPlan:
        active_session_id, request_for_routing = self._prepare_chat_request(request, session_id=session_id)
        if self._request_requires_tool_protocol(request_for_routing):
            payload, headers = self._execute_chat_completion(request_for_routing, session_id=active_session_id)
            self.state_store.save_chat_session(active_session_id, self._chat_session_messages(request_for_routing, payload))
            headers["Cache-Control"] = "no-cache"
            headers["X-Hermes-Session-Id"] = active_session_id
            return StreamPlan(body=self._synthetic_chat_stream_body(request_for_routing.model, payload), headers=headers)
        candidate, stream_result, first_chunk, chunk_iter = self._open_chat_stream(request_for_routing, session_id=active_session_id)
        request_shape = self._request_debug_shape(self._chat_request_payload(request_for_routing))
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
            saw_finish_reason = False
            try:
                if first_chunk:
                    for payload in self._chat_stream_payloads_from_event(
                        completion_id,
                        created,
                        request_for_routing.model,
                        first_chunk,
                    ):
                        if self._chunk_has_finish_reason(payload):
                            saw_finish_reason = True
                        yield f"data: {json.dumps(payload)}\n\n"
                for chunk in chunk_iter:
                    for payload in self._chat_stream_payloads_from_event(
                        completion_id,
                        created,
                        request_for_routing.model,
                        chunk,
                    ):
                        if self._chunk_has_finish_reason(payload):
                            saw_finish_reason = True
                        yield f"data: {json.dumps(payload)}\n\n"
            except NormalizedProviderError as exc:
                self._record_failure(
                    candidate,
                    request_for_routing.model,
                    exc,
                    latency_ms=round((time.monotonic() - started_at) * 1000, 2),
                    is_fallback=candidate.is_fallback,
                    zero_output=not self._stream_state_has_output(stream_result.state),
                    request_shape=request_shape,
                )
                raise
            latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            first_text_latency_ms = stream_result.state.first_text_latency_ms or latency_ms
            final_payload = stream_result.state.final_payload or self._chat_payload_from_stream_state(
                request_for_routing.model,
                stream_result.backend_model,
                stream_result.state,
            )
            self._record_success(
                candidate,
                request_for_routing.model,
                latency_ms=latency_ms,
                first_text_latency_ms=first_text_latency_ms,
                is_fallback=candidate.is_fallback,
                details={"score_breakdown": candidate.score_breakdown, "request_shape": request_shape},
            )
            self.state_store.save_chat_session(active_session_id, self._chat_session_messages(request_for_routing, final_payload))
            if not saw_finish_reason:
                finish_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request_for_routing.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": self._chat_finish_reason(final_payload),
                        }
                    ],
                    "usage": self._chat_usage(final_payload),
                }
                yield f"data: {json.dumps(finish_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamPlan(body=stream_body(), headers=headers)

    def responses_create(self, request: ResponsesRequest) -> tuple[dict[str, Any], dict[str, str]]:
        prepared = self._prepare_responses_request(request)
        payload, headers = self._execute_chat_completion(prepared.chat_request)
        response_id = f"resp_{uuid.uuid4().hex[:28]}"
        response_payload = self._responses_payload(response_id, prepared, payload)
        conversation_history = list(prepared.conversation_history)
        conversation_history.append(self._chat_message_from_payload(payload))
        if request.store:
            self.state_store.put_response(response_id, response_payload, conversation_history=conversation_history, instructions=prepared.instructions)
            if request.conversation:
                self.state_store.set_conversation_response(request.conversation, response_id)
        headers["X-Hermes-Session-Id"] = headers.get("X-Hermes-Session-Id", str(uuid.uuid4()))
        return response_payload, headers

    def responses_create_stream(self, request: ResponsesRequest) -> StreamPlan:
        prepared = self._prepare_responses_request(request)
        response_id = f"resp_{uuid.uuid4().hex[:28]}"
        if self._request_requires_tool_protocol(prepared.chat_request):
            final_chat_payload, headers = self._execute_chat_completion(prepared.chat_request)
            final_response_payload = self._responses_payload(response_id, prepared, final_chat_payload)
            if prepared.request.store:
                conversation_history = list(prepared.conversation_history)
                conversation_history.append(self._chat_message_from_payload(final_chat_payload))
                self.state_store.put_response(
                    response_id,
                    final_response_payload,
                    conversation_history=conversation_history,
                    instructions=prepared.instructions,
                )
                if prepared.request.conversation:
                    self.state_store.set_conversation_response(prepared.request.conversation, response_id)
            response_headers = {
                "Cache-Control": "no-cache",
                "X-Ghostship-Router-Backend-Provider": headers.get("X-Ghostship-Router-Backend-Provider", ""),
                "X-Ghostship-Router-Backend-Model": headers.get("X-Ghostship-Router-Backend-Model", ""),
            }
            if headers.get("X-Ghostship-Router-First-Text-Latency-Ms"):
                response_headers["X-Ghostship-Router-First-Text-Latency-Ms"] = headers["X-Ghostship-Router-First-Text-Latency-Ms"]
            return StreamPlan(body=self._synthetic_responses_stream_body(final_response_payload), headers=response_headers)
        candidate, stream_result, first_chunk, chunk_iter = self._open_chat_stream(prepared.chat_request)
        request_shape = self._request_debug_shape(self._chat_request_payload(prepared.chat_request))
        response_headers = {
            "Cache-Control": "no-cache",
            "X-Ghostship-Router-Backend-Provider": stream_result.provider,
            "X-Ghostship-Router-Backend-Model": stream_result.backend_model,
        }
        if stream_result.state.first_text_latency_ms is not None:
            response_headers["X-Ghostship-Router-First-Text-Latency-Ms"] = str(stream_result.state.first_text_latency_ms)

        def stream_body() -> Iterator[str]:
            sequence_number = 0
            created_at = int(time.time())
            output_items: list[dict[str, Any]] = []
            message_item_id = f"msg_{uuid.uuid4().hex[:24]}"
            reasoning_item_id = f"rs_{uuid.uuid4().hex[:24]}"
            message_started = False
            reasoning_started = False
            tool_output_indices: dict[int, int] = {}
            response_stub = self._responses_response_stub(response_id, prepared, created_at, output_items)
            yield self._sse_event("response.created", {"response": response_stub, "sequence_number": sequence_number, "type": "response.created"})
            sequence_number += 1

            started_at = time.monotonic()
            finish_reason: str | None = None
            try:
                for event in chain(() if first_chunk is None else (first_chunk,), chunk_iter):
                    if isinstance(event.reasoning, str) and event.reasoning:
                        if not reasoning_started:
                            output_items.append(
                                {
                                    "id": reasoning_item_id,
                                    "type": "reasoning",
                                    "summary": [],
                                    "content": [],
                                    "status": "in_progress",
                                }
                            )
                            yield self._sse_event(
                                "response.output_item.added",
                                {
                                    "item": output_items[-1],
                                    "output_index": len(output_items) - 1,
                                    "sequence_number": sequence_number,
                                    "type": "response.output_item.added",
                                },
                            )
                            sequence_number += 1
                            reasoning_started = True
                        yield self._sse_event(
                            "response.reasoning_text.delta",
                            {
                                "content_index": 0,
                                "delta": event.reasoning,
                                "item_id": reasoning_item_id,
                                "output_index": 0,
                                "sequence_number": sequence_number,
                                "type": "response.reasoning_text.delta",
                            },
                        )
                        sequence_number += 1
                    if isinstance(event.content, str) and event.content:
                        if not message_started:
                            output_items.append(
                                {
                                    "id": message_item_id,
                                    "type": "message",
                                    "role": "assistant",
                                    "status": "in_progress",
                                    "content": [],
                                }
                            )
                            message_index = len(output_items) - 1
                            yield self._sse_event(
                                "response.output_item.added",
                                {
                                    "item": output_items[-1],
                                    "output_index": message_index,
                                    "sequence_number": sequence_number,
                                    "type": "response.output_item.added",
                                },
                            )
                            sequence_number += 1
                            message_part = {"type": "output_text", "text": "", "annotations": []}
                            output_items[message_index]["content"].append(message_part)
                            yield self._sse_event(
                                "response.content_part.added",
                                {
                                    "content_index": 0,
                                    "item_id": message_item_id,
                                    "output_index": message_index,
                                    "part": message_part,
                                    "sequence_number": sequence_number,
                                    "type": "response.content_part.added",
                                },
                            )
                            sequence_number += 1
                            message_started = True
                        message_index = next(index for index, item in enumerate(output_items) if item.get("id") == message_item_id)
                        message_part = output_items[message_index]["content"][0]
                        message_part["text"] += event.content
                        yield self._sse_event(
                            "response.output_text.delta",
                            {
                                "content_index": 0,
                                "delta": event.content,
                                "item_id": message_item_id,
                                "logprobs": [],
                                "output_index": message_index,
                                "sequence_number": sequence_number,
                                "type": "response.output_text.delta",
                            },
                        )
                        sequence_number += 1
                    if isinstance(event.tool_calls, list):
                        for raw_tool_call in event.tool_calls:
                            if not isinstance(raw_tool_call, dict):
                                continue
                            raw_index = int(raw_tool_call.get("index") or 0)
                            output_index = tool_output_indices.get(raw_index)
                            if output_index is None:
                                tool_item = self._responses_function_call_item(raw_tool_call)
                                output_items.append(tool_item)
                                output_index = len(output_items) - 1
                                tool_output_indices[raw_index] = output_index
                                yield self._sse_event(
                                    "response.output_item.added",
                                    {
                                        "item": tool_item,
                                        "output_index": output_index,
                                        "sequence_number": sequence_number,
                                        "type": "response.output_item.added",
                                    },
                                )
                                sequence_number += 1
                            else:
                                tool_item = output_items[output_index]
                                function = raw_tool_call.get("function") if isinstance(raw_tool_call.get("function"), dict) else {}
                                if raw_tool_call.get("id"):
                                    tool_item["id"] = raw_tool_call["id"]
                                if function.get("name"):
                                    tool_item["name"] += str(function["name"])
                                if function.get("arguments"):
                                    tool_item["arguments"] += str(function["arguments"])
                            function = raw_tool_call.get("function") if isinstance(raw_tool_call.get("function"), dict) else {}
                            arguments_delta = function.get("arguments")
                            if isinstance(arguments_delta, str) and arguments_delta:
                                yield self._sse_event(
                                    "response.function_call_arguments.delta",
                                    {
                                        "delta": arguments_delta,
                                        "item_id": tool_item["id"],
                                        "output_index": output_index,
                                        "sequence_number": sequence_number,
                                        "type": "response.function_call_arguments.delta",
                                    },
                                )
                                sequence_number += 1
                    if isinstance(event.finish_reason, str) and event.finish_reason:
                        finish_reason = event.finish_reason
                        break
            except NormalizedProviderError as exc:
                self._record_failure(
                    candidate,
                    prepared.chat_request.model,
                    exc,
                    latency_ms=round((time.monotonic() - started_at) * 1000, 2),
                    is_fallback=candidate.is_fallback,
                    zero_output=not self._stream_state_has_output(stream_result.state),
                    request_shape=request_shape,
                )
                raise

            latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            first_text_latency_ms = stream_result.state.first_text_latency_ms or latency_ms
            final_chat_payload = stream_result.state.final_payload or self._chat_payload_from_stream_state(
                prepared.chat_request.model,
                stream_result.backend_model,
                stream_result.state,
                finish_reason=finish_reason,
            )
            self._record_success(
                candidate,
                prepared.chat_request.model,
                latency_ms=latency_ms,
                first_text_latency_ms=first_text_latency_ms,
                is_fallback=candidate.is_fallback,
                details={"score_breakdown": candidate.score_breakdown, "request_shape": request_shape},
            )
            final_response_payload = self._responses_payload(response_id, prepared, final_chat_payload)
            if prepared.request.store:
                conversation_history = list(prepared.conversation_history)
                conversation_history.append(self._chat_message_from_payload(final_chat_payload))
                self.state_store.put_response(
                    response_id,
                    final_response_payload,
                    conversation_history=conversation_history,
                    instructions=prepared.instructions,
                )
                if prepared.request.conversation:
                    self.state_store.set_conversation_response(prepared.request.conversation, response_id)
            yield self._sse_event(
                "response.completed",
                {
                    "response": final_response_payload,
                    "sequence_number": sequence_number,
                    "type": "response.completed",
                },
            )

        return StreamPlan(body=stream_body(), headers=response_headers)

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

    def _route_context(self, request_payload: dict[str, Any], *, session_id: str | None, response_api: bool = False) -> RouteContext:
        return RouteContext(
            request_id=f"route_{uuid.uuid4().hex[:24]}",
            session_id=session_id,
            shape_key=self._request_shape_key(request_payload, response_api=response_api),
            free_budget_seconds=max(0.0, float(self.config.free_total_budget_seconds)),
            free_started_at=time.monotonic(),
        )

    def _candidate_timeout(self, candidate: RouteCandidate, request_timeout: float | None, *, stream_first_byte: bool = False) -> float:
        if candidate.provider_name == "opencode-go":
            return float(request_timeout or self.config.fallback_timeout_seconds)
        free_limit = self.config.free_stream_first_byte_timeout_seconds if stream_first_byte else self.config.free_attempt_timeout_seconds
        upstream_limit = request_timeout or self.config.default_timeout
        return max(0.1, min(float(upstream_limit), float(free_limit)))

    def _free_budget_remaining(self, context: RouteContext) -> float:
        return context.free_budget_seconds - (time.monotonic() - context.free_started_at)

    def _normalize_timeout_error(self, exc: NormalizedProviderError, *, phase: str) -> NormalizedProviderError:
        if exc.category != "timeout":
            return exc
        category = {
            "connect": "connect_timeout",
            "first_byte": "first_byte_timeout",
            "read": "read_timeout",
            "request": "request_timeout",
        }.get(phase, "request_timeout")
        details = exc.details if isinstance(exc.details, dict) else {"message": str(exc)}
        return NormalizedProviderError(
            category,
            str(exc),
            provider=exc.provider,
            backend_model=exc.backend_model,
            retryable=exc.retryable,
            details={**details, "timeout_phase": phase},
        )

    def _call_provider_with_deadline(self, candidate: RouteCandidate, timeout_seconds: float, phase: str, call: Any) -> Any:
        future = self._deadline_executor.submit(call)
        try:
            return future.result(timeout=timeout_seconds)
        except futures.TimeoutError as exc:
            future.cancel()
            raise NormalizedProviderError(
                "timeout",
                f"{phase} timed out after {timeout_seconds} seconds",
                provider=candidate.provider_name,
                backend_model=candidate.backend_model,
                retryable=True,
                details={"timeout": timeout_seconds, "timeout_phase": phase, "deadline_enforced": True},
            ) from exc

    def _trace_route(self, event: str, **fields: Any) -> None:
        if not self.config.trace_routing:
            return
        logger.info("router_trace %s", json.dumps({"event": event, **fields}, sort_keys=True, default=str))

    def _execute_chat_completion(self, request: ChatCompletionRequest, *, session_id: str | None = None) -> tuple[dict[str, Any], dict[str, str]]:
        self._validate_tool_history(request)
        self._ensure_inventory_loaded_for_request()
        requires_tool_protocol = self._request_requires_tool_protocol(request)
        request_payload = self._chat_request_payload(request)
        request_payload.pop("timeout", None)
        context = self._route_context(request_payload, session_id=session_id)
        request_shape = self._request_debug_shape(request_payload)
        attempted: set[tuple[str, str]] = set()
        candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        if not candidates:
            wait_seconds = self._paced_wait_seconds(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol)
            if wait_seconds is not None:
                time.sleep(wait_seconds)
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        if not candidates:
            wait_seconds = self._paced_wait_seconds(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol)
            if wait_seconds is not None:
                time.sleep(wait_seconds)
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request.model}'."})
        request_payload["stream"] = False
        errors: list[dict[str, Any]] = []
        while candidates:
            index = len(attempted)
            candidate = candidates[0]
            attempted.add((candidate.provider_name, candidate.backend_model))
            attempt_timeout = self._candidate_timeout(candidate, request.timeout, stream_first_byte=False)
            if candidate.provider_name != "opencode-go" and self._free_budget_remaining(context) <= 0:
                self._record_skip(
                    candidate,
                    request.model,
                    "request_budget_exhausted",
                    request_shape=request_shape,
                    context=context,
                    candidate_rank=index,
                    attempt_timeout_seconds=attempt_timeout,
                )
                errors.append(
                    {
                        "provider": candidate.provider_name,
                        "backend_model": candidate.backend_model,
                        "category": "request_budget_exhausted",
                        "retryable": True,
                        "details": {"free_budget_seconds": context.free_budget_seconds},
                    }
                )
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                continue
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                candidates = self._resolve_remaining_candidates(request.model, attempted, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                continue
            self.state_store.note_provider_request(candidate.provider_name, next_request_at=time.time() + self._provider_spacing_seconds(candidate.provider_name))
            self._trace_route(
                "attempt",
                request_id=context.request_id,
                session_id=context.session_id,
                shape_key=context.shape_key,
                alias=request.model,
                provider=candidate.provider_name,
                backend_model=candidate.backend_model,
                rank=index,
                timeout_seconds=attempt_timeout,
            )
            start = time.monotonic()
            try:
                result = self._call_provider_with_deadline(
                    candidate,
                    attempt_timeout,
                    "request",
                    lambda: provider.chat_completions(candidate.backend_model, request_payload, timeout=attempt_timeout),
                )
                if requires_tool_protocol and self._payload_has_xml_tool_call(result.payload):
                    raise NormalizedProviderError(
                        "tool_protocol_mismatch",
                        "Provider returned XML pseudo-tool-call text for a tool-enabled request.",
                        provider=result.provider,
                        backend_model=result.backend_model,
                        retryable=True,
                        details={"xml_tool_call": True},
                    )
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                first_text_latency_ms = result.first_text_latency_ms or latency_ms
                self._record_success(
                    candidate,
                    request.model,
                    latency_ms=latency_ms,
                    first_text_latency_ms=first_text_latency_ms,
                    is_fallback=candidate.is_fallback or index > 0,
                    details={
                        "result_provider": result.provider,
                        "score_breakdown": candidate.score_breakdown,
                        "request_shape": request_shape,
                        "route": {
                            "request_id": context.request_id,
                            "session_id": context.session_id,
                            "shape_key": context.shape_key,
                            "candidate_rank": index,
                            "attempt_timeout_seconds": attempt_timeout,
                            "free_budget_seconds": context.free_budget_seconds,
                        },
                    },
                )
                self._remember_session_affinity(session_id, candidate)
                headers = {
                    "X-Ghostship-Router-Backend-Provider": result.provider,
                    "X-Ghostship-Router-Backend-Model": result.backend_model,
                    "X-Ghostship-Router-Latency-Ms": str(latency_ms),
                    "X-Ghostship-Router-First-Text-Latency-Ms": str(first_text_latency_ms),
                }
                return result.payload, headers
            except NormalizedProviderError as exc:
                exc = self._normalize_timeout_error(exc, phase="request")
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                self._record_failure(
                    candidate,
                    request.model,
                    exc,
                    latency_ms=latency_ms,
                    is_fallback=candidate.is_fallback or index > 0,
                    zero_output=True,
                    request_shape=request_shape,
                    context=context,
                    candidate_rank=index,
                    attempt_timeout_seconds=attempt_timeout,
                )
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
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                if not candidates:
                    wait_seconds = self._paced_wait_seconds(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol)
                    if wait_seconds is not None:
                        time.sleep(wait_seconds)
                        candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        raise RouterServiceError(
            self._status_code_for_attempt_failures(errors),
            {"message": f"All route candidates failed for alias '{request.model}'.", "attempts": errors},
        )

    def _open_chat_stream(
        self,
        request: ChatCompletionRequest,
        *,
        session_id: str | None = None,
    ) -> tuple[RouteCandidate, ProviderChatStreamResult, ProviderChatStreamEvent | None, Iterator[ProviderChatStreamEvent]]:
        self._validate_tool_history(request)
        self._ensure_inventory_loaded_for_request()
        requires_tool_protocol = self._request_requires_tool_protocol(request)
        request_payload = self._chat_request_payload(request)
        request_payload.pop("timeout", None)
        context = self._route_context(request_payload, session_id=session_id)
        request_shape = self._request_debug_shape(request_payload)
        attempted: set[tuple[str, str]] = set()
        candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        if not candidates:
            wait_seconds = self._paced_wait_seconds(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol)
            if wait_seconds is not None:
                time.sleep(wait_seconds)
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request.model}'."})
        attempt_errors: list[dict[str, Any]] = []
        while candidates:
            index = len(attempted)
            candidate = candidates[0]
            attempted.add((candidate.provider_name, candidate.backend_model))
            attempt_timeout = self._candidate_timeout(candidate, request.timeout, stream_first_byte=True)
            if candidate.provider_name != "opencode-go" and self._free_budget_remaining(context) <= 0:
                self._record_skip(
                    candidate,
                    request.model,
                    "request_budget_exhausted",
                    request_shape=request_shape,
                    context=context,
                    candidate_rank=index,
                    attempt_timeout_seconds=attempt_timeout,
                )
                attempt_errors.append(
                    {
                        "provider": candidate.provider_name,
                        "backend_model": candidate.backend_model,
                        "category": "request_budget_exhausted",
                        "retryable": True,
                        "details": {"free_budget_seconds": context.free_budget_seconds},
                    }
                )
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                continue
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                candidates = self._resolve_remaining_candidates(request.model, attempted, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                continue
            self.state_store.note_provider_request(candidate.provider_name, next_request_at=time.time() + self._provider_spacing_seconds(candidate.provider_name))
            self._trace_route(
                "stream_open",
                request_id=context.request_id,
                session_id=context.session_id,
                shape_key=context.shape_key,
                alias=request.model,
                provider=candidate.provider_name,
                backend_model=candidate.backend_model,
                rank=index,
                timeout_seconds=attempt_timeout,
            )
            start = time.monotonic()
            try:
                stream_result, first_chunk, chunk_iter = self._call_provider_with_deadline(
                    candidate,
                    attempt_timeout,
                    "first_byte",
                    lambda: self._open_stream_first_chunk(provider, candidate.backend_model, request_payload, attempt_timeout),
                )
                self._remember_session_affinity(session_id, candidate)
                return candidate, stream_result, first_chunk, chunk_iter
            except NormalizedProviderError as exc:
                exc = self._normalize_timeout_error(exc, phase="first_byte")
                self._record_failure(
                    candidate,
                    request.model,
                    exc,
                    latency_ms=round((time.monotonic() - start) * 1000, 2),
                    is_fallback=candidate.is_fallback or index > 0,
                    zero_output=True,
                    request_shape=request_shape,
                    context=context,
                    candidate_rank=index,
                    attempt_timeout_seconds=attempt_timeout,
                )
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
                candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
                if not candidates:
                    wait_seconds = self._paced_wait_seconds(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol)
                    if wait_seconds is not None:
                        time.sleep(wait_seconds)
                        candidates = self._resolve_remaining_candidates(request.model, attempted, session_id=session_id, requires_tool_protocol=requires_tool_protocol, shape_key=context.shape_key)
        raise RouterServiceError(
            self._status_code_for_attempt_failures(attempt_errors),
            {"message": f"All route candidates failed for alias '{request.model}'.", "attempts": attempt_errors},
        )

    @staticmethod
    def _open_stream_first_chunk(
        provider: ChatProvider,
        backend_model: str,
        request_payload: dict[str, Any],
        attempt_timeout: float,
    ) -> tuple[ProviderChatStreamResult, ProviderChatStreamEvent | None, Iterator[ProviderChatStreamEvent]]:
        stream_result = provider.chat_completions_stream(
            backend_model,
            request_payload,
            timeout=attempt_timeout,
        )
        chunk_iter = iter(stream_result.chunks)
        try:
            first_chunk = next(chunk_iter)
        except StopIteration:
            first_chunk = None
        return stream_result, first_chunk, chunk_iter

    @staticmethod
    def _status_code_for_attempt_failures(errors: list[dict[str, Any]]) -> int:
        categories = [str(error.get("category") or "") for error in errors]
        if any(category in {"bad_request", "tool_choice_unsupported"} for category in categories):
            return 400
        return 503

    @classmethod
    def _request_debug_shape(cls, payload: dict[str, Any], *, response_api: bool = False) -> dict[str, Any]:
        messages = [message for message in payload.get("messages") or [] if isinstance(message, dict)]
        role_counts: dict[str, int] = {}
        assistant_tool_call_messages = 0
        assistant_reasoning_messages = 0
        tool_result_messages = 0
        null_content_messages = 0
        for message in messages:
            role = str(message.get("role") or "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
            if message.get("content") is None:
                null_content_messages += 1
            if role == "assistant" and isinstance(message.get("tool_calls"), list) and message["tool_calls"]:
                assistant_tool_call_messages += 1
            if role == "assistant" and ("reasoning_content" in message or "reasoning" in message):
                assistant_reasoning_messages += 1
            if role == "tool" or message.get("tool_call_id"):
                tool_result_messages += 1
        return {
            "model": payload.get("model"),
            "shape_key": cls._request_shape_key(payload, response_api=response_api),
            "stream": bool(payload.get("stream")),
            "message_count": len(messages),
            "role_counts": role_counts,
            "has_tools": bool(payload.get("tools")),
            "tool_count": len(payload.get("tools") or []) if isinstance(payload.get("tools"), list) else None,
            "tool_choice": payload.get("tool_choice"),
            "has_stream_options": "stream_options" in payload,
            "has_temperature": "temperature" in payload,
            "has_max_tokens": "max_tokens" in payload,
            "assistant_tool_call_messages": assistant_tool_call_messages,
            "assistant_reasoning_messages": assistant_reasoning_messages,
            "tool_result_messages": tool_result_messages,
            "null_content_messages": null_content_messages,
        }

    @staticmethod
    def _request_shape_key(payload: dict[str, Any], *, response_api: bool = False) -> str:
        messages = [message for message in payload.get("messages") or [] if isinstance(message, dict)]
        parts: list[str] = []
        if response_api:
            parts.append("responses")
        if bool(payload.get("stream")):
            parts.append("stream")
        has_tools = bool(payload.get("tools")) or payload.get("tool_choice") not in (None, "none")
        if has_tools:
            parts.append("tools")
        if any(message.get("role") == "tool" or message.get("tool_call_id") or message.get("tool_calls") for message in messages):
            parts.append("tool_history")
        if any("reasoning_content" in message or "reasoning" in message for message in messages):
            parts.append("reasoning")
        return "+".join(parts) if parts else "text"

    def _ensure_inventory_loaded_for_request(self) -> None:
        if self._inventory or not self.providers:
            return
        self.refresh_inventory(reason="request")

    def _prepare_chat_request(self, request: ChatCompletionRequest, *, session_id: str | None) -> tuple[str, ChatCompletionRequest]:
        active_session_id = session_id or str(uuid.uuid4())
        if not session_id:
            return active_session_id, request
        stored_messages = self.state_store.load_chat_session(session_id)
        if not stored_messages:
            return active_session_id, request
        request_messages = self._chat_request_payload(request)["messages"]
        system_messages = [message for message in request_messages if message.get("role") == "system"]
        non_system = [message for message in request_messages if message.get("role") != "system"]
        if non_system:
            merged = [*system_messages, *stored_messages, non_system[-1]]
        else:
            merged = [*system_messages, *stored_messages]
        return active_session_id, ChatCompletionRequest.model_validate({**self._chat_request_payload(request), "messages": merged})

    def _chat_session_messages(self, request: ChatCompletionRequest, payload: dict[str, Any]) -> list[dict[str, Any]]:
        messages = [self._chat_message_dump(message) for message in request.messages if message.role != "system"]
        messages.append(self._chat_message_from_payload(payload))
        return messages

    @staticmethod
    def _chat_message_dump(message: Any) -> dict[str, Any]:
        if hasattr(message, "model_dump"):
            dumped = message.model_dump(mode="json", exclude_none=True)
            role = getattr(message, "role", dumped.get("role"))
            content = getattr(message, "content", dumped.get("content"))
            tool_calls = getattr(message, "tool_calls", dumped.get("tool_calls"))
        else:
            dumped = {key: value for key, value in dict(message).items() if value is not None}
            role = dumped.get("role")
            content = dict(message).get("content") if isinstance(message, dict) else dumped.get("content")
            tool_calls = dumped.get("tool_calls")
        if role == "assistant" and isinstance(tool_calls, list):
            dumped["tool_calls"] = tool_calls
            if content is None:
                dumped["content"] = None
        return dumped

    def _chat_request_payload(self, request: ChatCompletionRequest) -> dict[str, Any]:
        payload = request.model_dump(mode="json", exclude_none=True)
        payload["messages"] = [self._chat_message_dump(message) for message in request.messages]
        return payload

    def _validate_tool_history(self, request: ChatCompletionRequest) -> None:
        pending: dict[str, int] = {}
        for index, raw_message in enumerate(request.messages):
            message = self._chat_message_dump(raw_message)
            role = message.get("role")
            if pending and role not in {"tool"}:
                missing = ", ".join(sorted(pending))
                raise RouterServiceError(400, {"message": f"Tool call history is incomplete before message {index}; missing tool outputs for: {missing}."})
            if role == "assistant":
                for tool_call in message.get("tool_calls") or []:
                    if not isinstance(tool_call, dict):
                        continue
                    call_id = str(tool_call.get("id") or tool_call.get("call_id") or "").strip()
                    if call_id:
                        pending[call_id] = index
            elif role == "tool":
                call_id = str(message.get("tool_call_id") or "").strip()
                if not call_id:
                    raise RouterServiceError(400, {"message": f"Tool message {index} is missing tool_call_id."})
                if call_id not in pending:
                    raise RouterServiceError(400, {"message": f"Tool message {index} references unknown tool_call_id '{call_id}'."})
                pending.pop(call_id, None)
        if pending:
            missing = ", ".join(sorted(pending))
            raise RouterServiceError(400, {"message": f"Tool call history is incomplete; missing tool outputs for: {missing}."})

    def _request_requires_tool_protocol(self, request: ChatCompletionRequest) -> bool:
        payload = self._chat_request_payload(request)
        tools = payload.get("tools")
        if isinstance(tools, list) and tools:
            return True
        if payload.get("tool_choice") not in (None, "none"):
            return True
        for message in payload.get("messages") or []:
            if not isinstance(message, dict):
                continue
            if message.get("role") == "tool" or message.get("tool_call_id") or message.get("tool_calls"):
                return True
        return False

    @staticmethod
    def _payload_has_xml_tool_call(payload: dict[str, Any]) -> bool:
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        values = [message.get("content"), message.get("reasoning_content"), message.get("reasoning")]
        text = "\n".join(value for value in values if isinstance(value, str)).lower()
        return "<tool_call" in text or "</tool_call" in text or "<attribute" in text or "</attribute" in text

    def _synthetic_chat_stream_body(self, model: str, payload: dict[str, Any]) -> Iterator[str]:
        completion_id = str(payload.get("id") or f"chatcmpl-{uuid.uuid4().hex[:29]}")
        created = int(payload.get("created") or time.time())
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        yield self._chat_stream_sse(completion_id, created, model, {"role": "assistant"})
        content = message.get("content")
        if isinstance(content, str) and content:
            yield self._chat_stream_sse(completion_id, created, model, {"content": content})
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            yield self._chat_stream_sse(completion_id, created, model, {"reasoning_content": reasoning})
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            yield self._chat_stream_sse(completion_id, created, model, {"tool_calls": tool_calls})
        finish_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": self._chat_finish_reason(payload)}],
            "usage": self._chat_usage(payload),
        }
        yield f"data: {json.dumps(finish_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    @staticmethod
    def _chat_stream_sse(completion_id: str, created: int, model: str, delta: dict[str, Any]) -> str:
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        return f"data: {json.dumps(chunk)}\n\n"

    def _synthetic_responses_stream_body(self, payload: dict[str, Any]) -> Iterator[str]:
        sequence_number = 0
        created = {
            **payload,
            "status": "in_progress",
            "output": [],
        }
        yield self._sse_event("response.created", {"response": created, "sequence_number": sequence_number, "type": "response.created"})
        sequence_number += 1
        for output_index, item in enumerate(payload.get("output") or []):
            yield self._sse_event(
                "response.output_item.added",
                {"item": item, "output_index": output_index, "sequence_number": sequence_number, "type": "response.output_item.added"},
            )
            sequence_number += 1
            if item.get("type") == "message":
                for content_index, part in enumerate(item.get("content") or []):
                    text = part.get("text") if isinstance(part, dict) else None
                    if isinstance(text, str) and text:
                        yield self._sse_event(
                            "response.output_text.delta",
                            {
                                "content_index": content_index,
                                "delta": text,
                                "item_id": item.get("id"),
                                "output_index": output_index,
                                "sequence_number": sequence_number,
                                "type": "response.output_text.delta",
                            },
                        )
                        sequence_number += 1
            if item.get("type") == "function_call" and item.get("arguments"):
                yield self._sse_event(
                    "response.function_call_arguments.delta",
                    {
                        "delta": item.get("arguments"),
                        "item_id": item.get("id"),
                        "output_index": output_index,
                        "sequence_number": sequence_number,
                        "type": "response.function_call_arguments.delta",
                    },
                )
                sequence_number += 1
        yield self._sse_event("response.completed", {"response": payload, "sequence_number": sequence_number, "type": "response.completed"})

    def _assistant_text_from_payload(self, payload: dict[str, Any]) -> str:
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [str(item.get("text", "")) for item in content if isinstance(item, dict)]
            return "\n".join(part for part in parts if part)
        return str(content or "")

    def _chat_message_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        chat_message: dict[str, Any] = {
            "role": str(message.get("role") or "assistant"),
            "content": self._assistant_text_from_payload(payload),
        }
        if isinstance(message.get("tool_calls"), list):
            chat_message["tool_calls"] = message["tool_calls"]
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            chat_message["reasoning_content"] = reasoning
        return chat_message

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

    def _chat_payload_from_stream_state(
        self,
        model_alias: str,
        backend_model: str,
        state: Any,
        *,
        finish_reason: str | None = None,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "assistant", "content": state.emitted_text}
        if getattr(state, "emitted_reasoning", ""):
            message["reasoning_content"] = state.emitted_reasoning
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": backend_model or model_alias,
            "choices": [{"index": 0, "message": message, "finish_reason": finish_reason or "stop"}],
            "usage": state.usage,
        }

    def _chat_usage(self, payload: dict[str, Any]) -> dict[str, int]:
        usage = payload.get("usage") or {}
        return {
            "prompt_tokens": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }

    def _chat_finish_reason(self, payload: dict[str, Any]) -> str:
        finish_reason = ((payload.get("choices") or [{}])[0].get("finish_reason") or None)
        return finish_reason if isinstance(finish_reason, str) and finish_reason else "stop"

    def _chunk_has_finish_reason(self, payload: dict[str, Any]) -> bool:
        for choice in payload.get("choices") or []:
            if isinstance(choice, dict) and isinstance(choice.get("finish_reason"), str) and choice.get("finish_reason"):
                return True
        return False

    def _chat_stream_payloads_from_event(
        self,
        completion_id: str,
        created: int,
        model: str,
        event: ProviderChatStreamEvent,
    ) -> list[dict[str, Any]]:
        if event.raw_chunk:
            payload = json.loads(json.dumps(event.raw_chunk))
            payload.setdefault("id", completion_id)
            payload.setdefault("object", "chat.completion.chunk")
            payload.setdefault("created", created)
            payload["model"] = model
            for choice in payload.get("choices") or []:
                if not isinstance(choice, dict):
                    continue
                delta = choice.get("delta")
                if isinstance(delta, dict) and delta.get("role") == "assistant":
                    delta.pop("role", None)
            return [payload]

        delta: dict[str, Any] = {}
        if isinstance(event.content, str) and event.content:
            delta["content"] = event.content
        if isinstance(event.reasoning, str) and event.reasoning:
            delta["reasoning_content"] = event.reasoning
        if isinstance(event.tool_calls, list) and event.tool_calls:
            delta["tool_calls"] = event.tool_calls
        if not delta and event.usage:
            return [
                {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [],
                    "usage": event.usage,
                }
            ]
        if not delta and not event.finish_reason:
            return []
        return [
            {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": event.finish_reason}],
                **({"usage": event.usage} if event.usage else {}),
            }
        ]

    def _record_failure(
        self,
        candidate: RouteCandidate,
        alias: str,
        exc: NormalizedProviderError,
        *,
        latency_ms: float | None,
        is_fallback: bool,
        zero_output: bool,
        request_shape: dict[str, Any] | None = None,
        context: RouteContext | None = None,
        candidate_rank: int | None = None,
        attempt_timeout_seconds: float | None = None,
    ) -> None:
        logger.warning(
            "router candidate failed: provider=%s backend_model=%s category=%s retryable=%s",
            exc.provider,
            exc.backend_model,
            exc.category,
            exc.retryable,
        )
        self.state_store.apply_failure(
            candidate.provider_name,
            candidate.backend_model,
            category=exc.category,
            retryable=exc.retryable,
            cooldown_model=self._should_apply_model_cooldown(exc),
        )
        provider_throttle: dict[str, Any] | None = None
        throttle_until = self._provider_throttle_until(candidate.provider_name, exc)
        if throttle_until is not None:
            provider_throttle = self.state_store.apply_provider_throttle(
                candidate.provider_name,
                category=exc.category,
                throttle_until=throttle_until,
                details=exc.details,
            )
        provider_exhaustion = self.state_store.record_provider_exhaustion(
            candidate.provider_name,
            backend_model=candidate.backend_model,
            category=exc.category,
            details=exc.details,
            zero_output=zero_output,
            suspect_window_seconds=self.config.provider_suspect_window_seconds,
            disable_seconds=self.config.provider_disable_seconds,
            probe_escalation_factor=self.config.provider_probe_escalation_factor,
            max_disable_seconds=self.config.provider_max_disable_seconds,
        )
        shape_health = None
        shape_key = context.shape_key if context is not None else (request_shape or {}).get("shape_key")
        if shape_key and candidate.provider_name != "opencode-go":
            shape_health = self.state_store.record_shape_result(
                candidate.provider_name,
                candidate.backend_model,
                str(shape_key),
                success=False,
                category=exc.category,
                latency_ms=latency_ms,
                first_text_latency_ms=None,
            )
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
                details={
                    "provider_error": exc.details,
                    "score_breakdown": candidate.score_breakdown,
                    "zero_output": zero_output,
                    "provider_exhaustion": provider_exhaustion,
                    "provider_throttle": provider_throttle,
                    "request_shape": request_shape,
                    "shape_health": shape_health,
                    "route": {
                        "request_id": context.request_id if context else None,
                        "session_id": context.session_id if context else None,
                        "shape_key": shape_key,
                        "candidate_rank": candidate_rank,
                        "attempt_timeout_seconds": attempt_timeout_seconds,
                        "free_budget_seconds": context.free_budget_seconds if context else None,
                        "free_budget_remaining_seconds": self._free_budget_remaining(context) if context else None,
                    },
                },
                created_at=time.time(),
            )
        )

    def _record_skip(
        self,
        candidate: RouteCandidate,
        alias: str,
        category: str,
        *,
        request_shape: dict[str, Any] | None,
        context: RouteContext,
        candidate_rank: int,
        attempt_timeout_seconds: float,
    ) -> None:
        self.state_store.record_attempt(
            RouteEvent(
                alias=alias,
                provider_name=candidate.provider_name,
                backend_model=candidate.backend_model,
                success=False,
                retryable=True,
                is_fallback=candidate.is_fallback,
                category=category,
                latency_ms=0.0,
                first_text_latency_ms=None,
                details={
                    "skip_reason": category,
                    "score_breakdown": candidate.score_breakdown,
                    "request_shape": request_shape,
                    "route": {
                        "request_id": context.request_id,
                        "session_id": context.session_id,
                        "shape_key": context.shape_key,
                        "candidate_rank": candidate_rank,
                        "attempt_timeout_seconds": attempt_timeout_seconds,
                        "free_budget_seconds": context.free_budget_seconds,
                        "free_budget_remaining_seconds": self._free_budget_remaining(context),
                    },
                },
                created_at=time.time(),
            )
        )

    def _record_success(
        self,
        candidate: RouteCandidate,
        alias: str,
        *,
        latency_ms: float | None,
        first_text_latency_ms: float | None,
        is_fallback: bool,
        details: dict[str, Any],
    ) -> None:
        self.state_store.apply_success(
            candidate.provider_name,
            candidate.backend_model,
            latency_ms=latency_ms,
            first_text_latency_ms=first_text_latency_ms,
        )
        request_shape = details.get("request_shape") if isinstance(details.get("request_shape"), dict) else {}
        shape_key = str(request_shape.get("shape_key") or "")
        slow_success = candidate.provider_name != "opencode-go" and (
            (first_text_latency_ms is not None and first_text_latency_ms >= self.config.provider_slow_first_text_threshold_ms)
            or (latency_ms is not None and latency_ms >= self.config.provider_slow_total_threshold_ms)
        )
        if shape_key and candidate.provider_name != "opencode-go":
            details = {
                **details,
                "shape_health": self.state_store.record_shape_result(
                    candidate.provider_name,
                    candidate.backend_model,
                    shape_key,
                    success=True,
                    category="slow_success" if slow_success else None,
                    latency_ms=latency_ms,
                    first_text_latency_ms=first_text_latency_ms,
                    slow_success=slow_success,
                ),
            }
        self._apply_provider_health_guards(candidate.provider_name)
        self.state_store.record_attempt(
            RouteEvent(
                alias=alias,
                provider_name=candidate.provider_name,
                backend_model=candidate.backend_model,
                success=True,
                retryable=False,
                is_fallback=is_fallback,
                category=None,
                latency_ms=latency_ms,
                first_text_latency_ms=first_text_latency_ms,
                details=details,
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
            item_type = item.get("type")
            if item_type == "function_call":
                function_name = str(item.get("name") or "").strip()
                if not function_name:
                    continue
                arguments = item.get("arguments", "{}")
                if not isinstance(arguments, str):
                    arguments = json.dumps(arguments)
                call_id = str(item.get("call_id") or f"call_{uuid.uuid4().hex[:24]}")
                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": call_id,
                                "call_id": call_id,
                                "type": "function",
                                "function": {"name": function_name, "arguments": arguments},
                            }
                        ],
                    }
                )
                continue
            if item_type == "function_call_output":
                call_id = str(item.get("call_id") or "").strip()
                if not call_id:
                    continue
                messages.append({"role": "tool", "tool_call_id": call_id, "content": str(item.get("output") or "")})
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

    @staticmethod
    def _stream_state_has_output(state: Any) -> bool:
        if getattr(state, "emitted_text", ""):
            return True
        if getattr(state, "emitted_reasoning", ""):
            return True
        final_payload = getattr(state, "final_payload", None)
        if isinstance(final_payload, dict):
            message = ((final_payload.get("choices") or [{}])[0].get("message") or {})
            if message.get("content") or message.get("reasoning_content") or message.get("tool_calls"):
                return True
        return False

    def _prepare_responses_request(self, request: ResponsesRequest) -> PreparedResponsesRequest:
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
        passthrough = dict(request.model_extra or {})
        max_output_tokens = passthrough.pop("max_output_tokens", None)
        passthrough.pop("stream", None)
        passthrough.pop("store", None)
        chat_request = ChatCompletionRequest.model_validate(
            {
                "model": request.model,
                "messages": chat_messages,
                "max_tokens": max_output_tokens,
                "timeout": request.timeout,
                **passthrough,
            }
        )
        return PreparedResponsesRequest(
            chat_request=chat_request,
            instructions=instructions,
            conversation_history=[message for message in chat_messages if message.get("role") != "system"],
            previous_response_id=previous_response_id,
            request=request,
        )

    def _responses_payload(self, response_id: str, prepared: PreparedResponsesRequest, chat_payload: dict[str, Any]) -> dict[str, Any]:
        output: list[dict[str, Any]] = []
        message = ((chat_payload.get("choices") or [{}])[0].get("message") or {})
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            output.append(
                {
                    "id": f"rs_{uuid.uuid4().hex[:24]}",
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": reasoning}],
                    "content": [{"type": "reasoning_text", "text": reasoning}],
                    "status": "completed",
                }
            )
        assistant_text = self._assistant_text_from_payload(chat_payload)
        if assistant_text:
            output.append(
                {
                    "id": f"msg_{uuid.uuid4().hex[:24]}",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": assistant_text, "annotations": []}],
                }
            )
        for tool_call in message.get("tool_calls") or []:
            if not isinstance(tool_call, dict):
                continue
            output.append(self._responses_function_call_item(tool_call, completed=True))
        model_extra = prepared.request.model_extra or {}
        return {
            "id": response_id,
            "created_at": int(time.time()),
            "error": None,
            "incomplete_details": None,
            "instructions": prepared.instructions,
            "model": prepared.request.model,
            "object": "response",
            "output": output,
            "parallel_tool_calls": bool(model_extra.get("parallel_tool_calls", True)),
            "tool_choice": model_extra.get("tool_choice") or "auto",
            "tools": model_extra.get("tools") or [],
            "previous_response_id": prepared.previous_response_id,
            "status": "completed",
            "text": {"format": {"type": "text"}},
            "truncation": prepared.request.truncation,
            "usage": {
                "input_tokens": int((chat_payload.get("usage") or {}).get("prompt_tokens") or (chat_payload.get("usage") or {}).get("input_tokens") or 0),
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens": int((chat_payload.get("usage") or {}).get("completion_tokens") or (chat_payload.get("usage") or {}).get("output_tokens") or 0),
                "output_tokens_details": {"reasoning_tokens": 0},
                "total_tokens": int((chat_payload.get("usage") or {}).get("total_tokens") or 0),
            },
        }

    def _responses_response_stub(
        self,
        response_id: str,
        prepared: PreparedResponsesRequest,
        created_at: int,
        output: list[dict[str, Any]],
    ) -> dict[str, Any]:
        model_extra = prepared.request.model_extra or {}
        return {
            "id": response_id,
            "created_at": created_at,
            "error": None,
            "incomplete_details": None,
            "instructions": prepared.instructions,
            "model": prepared.request.model,
            "object": "response",
            "output": output,
            "parallel_tool_calls": bool(model_extra.get("parallel_tool_calls", True)),
            "tool_choice": model_extra.get("tool_choice") or "auto",
            "tools": model_extra.get("tools") or [],
            "previous_response_id": prepared.previous_response_id,
            "status": "in_progress",
            "text": {"format": {"type": "text"}},
            "truncation": prepared.request.truncation,
            "usage": None,
        }

    def _responses_function_call_item(self, tool_call: dict[str, Any], *, completed: bool = False) -> dict[str, Any]:
        function = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
        raw_id = str(tool_call.get("id") or "")
        call_id = str(tool_call.get("call_id") or raw_id or f"call_{uuid.uuid4().hex[:24]}")
        item_id = raw_id if raw_id.startswith("fc_") else f"fc_{call_id.removeprefix('call_')}"
        return {
            "id": item_id,
            "type": "function_call",
            "call_id": call_id,
            "name": str(function.get("name") or ""),
            "arguments": str(function.get("arguments") or ""),
            "status": "completed" if completed else "in_progress",
        }

    def _sse_event(self, event_type: str, payload: dict[str, Any]) -> str:
        return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

    def refresh_inventory(self, *, reason: str) -> list[ProviderModel]:
        with self._refresh_lock:
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
            if errors:
                self._log_event("refresh_partial", reason=reason, model_count=len(self._inventory), errors=errors)
            else:
                self._log_event("refresh_complete", reason=reason, model_count=len(self._inventory))
            return self._inventory

    def debug_state(self) -> dict[str, Any]:
        return {
            "providers": list(self._provider_names),
            "provider_priority": list(self.config.provider_priority),
            "last_refresh_reason": self._last_refresh_reason,
            "last_refresh_at": self._last_refresh_at,
            "last_refresh_error": self._last_refresh_error,
            "inventory_ttl_seconds": self.config.inventory_ttl_seconds,
            "refresh_interval_seconds": self.config.refresh_interval_seconds,
            "session_affinity": self._session_affinity,
            "policy": {
                "providers": [
                    {
                        "provider_name": policy.provider_name,
                        "seeded_models": list(policy.seeded_models),
                        "unused_models": list(policy.unused_models),
                        "daily_reset_hours": policy.daily_reset_hours,
                    }
                    for policy in self.config.provider_seed_policies
                ],
                "aliases": [
                    {
                        "name": alias.name,
                        "preferred_models": list(alias.preferred_models),
                        "selection": "dynamic-opencode-go-catalog",
                    }
                    for alias in self.config.aliases
                ],
            },
            "state": self.state_store.snapshot(),
        }

    def debug_events(self) -> list[dict[str, Any]]:
        return self.state_store.get_recent_events(self.config.debug_event_limit)

    def debug_route_events(
        self,
        *,
        limit: int | None = None,
        alias: str | None = None,
        provider_name: str | None = None,
        backend_model: str | None = None,
        category: str | None = None,
        since: float | None = None,
        success: bool | None = None,
    ) -> dict[str, Any]:
        resolved_limit = max(1, min(int(limit or self.config.debug_event_limit), 500))
        events = self.state_store.get_route_events(
            limit=resolved_limit,
            alias=alias,
            provider_name=provider_name,
            backend_model=backend_model,
            category=category,
            since=since,
            success=success,
        )
        return {
            "limit": resolved_limit,
            "filters": {
                "alias": alias,
                "provider_name": provider_name,
                "backend_model": backend_model,
                "category": category,
                "since": since,
                "success": success,
            },
            "events": events,
        }

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
                    "next_request_at": state.get("next_request_at", 0),
                    "disable_reason": state.get("disable_reason"),
                    "breaker_level": state.get("breaker_level", 0),
                    "probe_mode": self._provider_in_probe_mode(provider_name, state=state),
                    "pacing_active": self._provider_is_pacing(provider_name, state=state),
                    "throttle_reason": state.get("throttle_reason"),
                    "throttle_streak": state.get("throttle_streak", 0),
                    "suppression_source": self._provider_suppression_source(provider_name, state=state),
                    "rpm": self._provider_rpm_state(provider_name),
                    "suspect_backend_model": state.get("suspect_backend_model"),
                    "suspect_category": state.get("suspect_category"),
                    "suspect_at": state.get("suspect_at"),
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

    def debug_summary(self) -> dict[str, Any]:
        provider_state = self.state_store.get_provider_state()
        exposed_models = [model.id for model in self._opencode_go_models() if self._free_equivalent_models(model.id)]
        primary_alias = self.config.aliases[0].name if self.config.aliases else (exposed_models[0] if exposed_models else "deepseek-v4-pro")
        provider_order = list(self._provider_order())
        enabled_providers = [provider_name for provider_name in self._provider_names if self._provider_enabled(provider_name)]
        providers: list[dict[str, Any]] = []
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            provider_inventory = [model for model in self._inventory_for_all() if model.provider == provider_name]
            providers.append(
                {
                    "provider_name": provider_name,
                    "enabled": self._provider_enabled(provider_name),
                    "cooling_down": self._provider_is_cooling_down(provider_name, state=state),
                    "pacing_active": self._provider_is_pacing(provider_name, state=state),
                    "probe_mode": self._provider_in_probe_mode(provider_name, state=state),
                    "suppression_source": self._provider_suppression_source(provider_name, state=state),
                    "rpm": self._provider_rpm_state(provider_name),
                    "stats": state,
                    "inventory_counts": {
                        "total": len(provider_inventory),
                        "free": sum(1 for model in provider_inventory if model.is_free),
                        "seeded": len(self._seeded_backend_ids_for_provider(provider_name)),
                    },
                    "active_candidates": [
                        item
                        for item in self.preview_routes(primary_alias)
                        if item["provider_name"] == provider_name
                    ],
                }
            )
        selected_candidates = self.preview_routes(primary_alias)
        return {
            "router": {
                "configured_providers": list(self.config.provider_priority),
                "available_providers": list(self._provider_names),
                "enabled_providers": enabled_providers,
                "provider_priority": provider_order,
                "auth_required": bool(self.config.api_key),
                "last_refresh_reason": self._last_refresh_reason,
                "last_refresh_at": self._last_refresh_at,
                "last_refresh_error": self._last_refresh_error,
                "rolling_route_stats": self.state_store.get_route_window_stats(
                    {"1m": 60.0, "5m": 300.0, "1h": 3600.0, "daily": 86400.0}
                ),
            },
            "providers": providers,
            "aliases": {
                alias: {
                    "provider_order": provider_order,
                    "selected_provider": (selected_candidates[0]["provider_name"] if alias == primary_alias and selected_candidates else None),
                    "selected_candidates": selected_candidates if alias == primary_alias else self.preview_routes(alias),
                    "providers": self.debug_rankings(alias)["providers"],
                }
                for alias in exposed_models
            },
        }

    def debug_rankings(self, alias: str) -> dict[str, Any]:
        if alias in {"auxiliary", "coding", "agentic", "vision", "tts"}:
            raise RouterServiceError(404, {"message": f"Logical model alias '{alias}' is retired. Use an exposed OpenCode Go model id."})
        if self._opencode_go_model(alias) is None:
            raise RouterServiceError(404, {"message": f"Unknown OpenCode Go model id '{alias}'."})
        selected_keys = {
            (candidate["provider_name"], candidate["backend_model"])
            for candidate in self.preview_routes(alias)
        }
        providers: list[dict[str, Any]] = []
        equivalents_by_provider: dict[str, list[ProviderModel]] = {}
        for model in self._free_equivalent_models(alias):
            equivalents_by_provider.setdefault(model.provider, []).append(model)
        go_model = self._opencode_go_model(alias)
        if go_model is not None:
            equivalents_by_provider.setdefault("opencode-go", []).append(go_model)
        for provider_name in self.config.provider_priority:
            provider_models = equivalents_by_provider.get(provider_name, [])
            if not provider_models:
                continue
            entries: list[dict[str, Any]] = []
            for model in provider_models:
                entries.append(
                    {
                        "backend_model": model.id,
                        "configured": provider_name in self.providers,
                        "discovered": True,
                        "selected_for_routing": (provider_name, model.id) in selected_keys,
                        "is_free": bool(model.is_free),
                        "routable": self._model_is_routable(model, alias=alias),
                        "excluded_reason": self._ranked_model_exclusion_reason(
                            provider_name,
                            model.id,
                            alias=alias,
                            model=model,
                        ),
                    }
                )
            providers.append(
                {
                    "provider_name": provider_name,
                    "enabled": self._provider_enabled(provider_name),
                    "cooling_down": self._provider_is_cooling_down(provider_name),
                    "pacing": self._provider_is_pacing(provider_name),
                    "rpm": self._provider_rpm_state(provider_name),
                    "probe_mode": self._provider_in_probe_mode(provider_name),
                    "seeded": entries,
                    "active_candidates": [
                        item
                        for item in self.preview_routes(alias)
                        if item["provider_name"] == provider_name
                    ],
                }
            )
        return {"alias": alias, "providers": providers}

    def debug_inventory(self, category: str, *, alias: str = "deepseek-v4-pro") -> dict[str, Any]:
        if category not in {"seeded", "configured", "unconfigured", "inventory"}:
            raise RouterServiceError(404, {"message": f"Unknown inventory category '{category}'."})
        if self._opencode_go_model(alias) is None:
            fallback_alias = self.config.aliases[0].name if self.config.aliases else ""
            alias = fallback_alias if fallback_alias and self._opencode_go_model(fallback_alias) is not None else alias
        if self._opencode_go_model(alias) is None:
            return {"alias": alias, "category": category, "providers": {}}
        providers: dict[str, list[dict[str, Any]]] = {}
        if category == "inventory":
            for model in self._inventory_for_all():
                providers.setdefault(model.provider, []).append(
                    {
                        "backend_model": model.id,
                        "is_free": model.is_free,
                        "seeded": model.id in self._seeded_backend_ids_for_provider(model.provider),
                        "metadata": model.metadata,
                    }
                )
            return {"alias": alias, "category": category, "providers": providers}
        dynamic_models = [*self._free_equivalent_models(alias)]
        go_model = self._opencode_go_model(alias)
        if go_model is not None:
            dynamic_models.append(go_model)
        for model in dynamic_models:
            provider_name = model.provider
            backend_model = model.id
            configured = provider_name in self.providers
            if category == "configured" and not configured:
                continue
            if category == "unconfigured" and configured:
                continue
            providers.setdefault(provider_name, []).append(
                {
                    "backend_model": backend_model,
                    "configured": configured,
                    "discovered": True,
                    "is_free": bool(model.is_free),
                    "rpm": self._provider_rpm_state(provider_name),
                    "metadata": model.metadata,
                }
            )
        return {"alias": alias, "category": category, "providers": providers}

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
            "overrides": self._model_override_payload(provider_name, backend_model),
        }

    def metrics_text(self) -> str:
        route_rows = self.state_store.get_route_metric_rows()
        refresh_rows = self.state_store.get_refresh_metric_rows()
        model_state = self.state_store.get_model_state()
        provider_state = self.state_store.get_provider_state()
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
        window_stats = self.state_store.get_route_window_stats({"1m": 60.0, "5m": 300.0, "1h": 3600.0, "daily": 86400.0})
        lines.extend(
            [
                "# HELP ghostship_router_window_attempts Rolling route attempts by window, provider, model, and result.",
                "# TYPE ghostship_router_window_attempts gauge",
            ]
        )
        for window_name, rows in window_stats.items():
            for row in rows:
                lines.append(
                    self._prom_metric(
                        "ghostship_router_window_attempts",
                        row["attempts"],
                        window=window_name,
                        provider=row["provider_name"],
                        backend_model=row["backend_model"],
                        result=("success" if row["success"] else "failure"),
                        category=(row["category"] or "none"),
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
                "# HELP ghostship_router_provider_pacing_active Whether a provider is currently delayed by pacing or temporary throttle.",
                "# TYPE ghostship_router_provider_pacing_active gauge",
            ]
        )
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            lines.append(
                self._prom_metric(
                    "ghostship_router_provider_pacing_active",
                    1 if self._provider_is_pacing(provider_name, state=state) else 0,
                    provider=provider_name,
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_provider_rpm_limit Configured sliding-window request-per-minute limit for free providers.",
                "# TYPE ghostship_router_provider_rpm_limit gauge",
            ]
        )
        for provider_name in self._provider_names:
            limit = self._provider_rpm_limit(provider_name)
            if limit is not None:
                lines.append(self._prom_metric("ghostship_router_provider_rpm_limit", limit, provider=provider_name))
        lines.extend(
            [
                "# HELP ghostship_router_provider_rpm_used Requests recorded in the last 60 seconds.",
                "# TYPE ghostship_router_provider_rpm_used gauge",
            ]
        )
        for provider_name in self._provider_names:
            limit = self._provider_rpm_limit(provider_name)
            if limit is not None:
                lines.append(self._prom_metric("ghostship_router_provider_rpm_used", self._provider_rpm_used(provider_name), provider=provider_name))
        lines.extend(
            [
                "# HELP ghostship_router_provider_probe_mode Whether a provider is in probe recovery mode.",
                "# TYPE ghostship_router_provider_probe_mode gauge",
            ]
        )
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            lines.append(
                self._prom_metric(
                    "ghostship_router_provider_probe_mode",
                    1 if self._provider_in_probe_mode(provider_name, state=state) else 0,
                    provider=provider_name,
                )
            )
        lines.extend(
            [
                "# HELP ghostship_router_provider_breaker_level Current provider exhaustion breaker level.",
                "# TYPE ghostship_router_provider_breaker_level gauge",
            ]
        )
        for provider_name in self._provider_names:
            state = provider_state.get(provider_name, {})
            lines.append(
                self._prom_metric(
                    "ghostship_router_provider_breaker_level",
                    state.get("breaker_level", 0) or 0,
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
                "# HELP ghostship_router_model_exhaustion_streak Current consecutive exhaustion streak for a backend model.",
                "# TYPE ghostship_router_model_exhaustion_streak gauge",
            ]
        )
        for key, state in model_state.items():
            provider_name, backend_model = key.split("::", 1)
            lines.append(
                self._prom_metric(
                    "ghostship_router_model_exhaustion_streak",
                    state.get("exhaustion_streak", 0) or 0,
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
        for model in self._opencode_go_models():
            if self._free_equivalent_models(model.id):
                lines.append(self._prom_metric("ghostship_router_candidate_count", len(self.preview_routes(model.id)), alias=model.id))
        return "\n".join(lines) + "\n"

    def preview_routes(self, alias: str, *, shape_key: str = "text", requires_tool_protocol: bool | None = None) -> list[dict[str, Any]]:
        try:
            candidates = self._resolve_candidates(
                alias,
                shape_key=shape_key,
                requires_tool_protocol=self._shape_key_requires_tool_protocol(shape_key) if requires_tool_protocol is None else requires_tool_protocol,
            )
        except RouterServiceError:
            return []
        return self._render_candidates(candidates)

    def debug_routes(self, alias: str, *, shape_key: str = "text") -> dict[str, Any]:
        if alias in {"auxiliary", "coding", "agentic", "vision", "tts"}:
            raise RouterServiceError(404, {"message": f"Logical model alias '{alias}' is retired. Use an exposed OpenCode Go model id."})
        if self._opencode_go_model(alias) is None:
            raise RouterServiceError(404, {"message": f"Unknown OpenCode Go model id '{alias}'."})
        requires_tool_protocol = self._shape_key_requires_tool_protocol(shape_key)
        candidates = self.preview_routes(alias, shape_key=shape_key, requires_tool_protocol=requires_tool_protocol)
        active_keys = {(item["provider_name"], item["backend_model"]) for item in candidates}
        skipped: list[dict[str, Any]] = []
        for model in [*self._free_equivalent_models(alias), *(go_model for go_model in [self._opencode_go_model(alias)] if go_model is not None)]:
            if (model.provider, model.id) in active_keys:
                continue
            skipped.append(
                {
                    "provider_name": model.provider,
                    "backend_model": model.id,
                    "is_free": bool(model.is_free),
                    "reason": self._ranked_model_exclusion_reason(
                        model.provider,
                        model.id,
                        alias=alias,
                        model=model,
                        shape_key=shape_key,
                        requires_tool_protocol=requires_tool_protocol,
                    ),
                    "state": self._candidate_state(model.provider, model.id, shape_key=shape_key),
                }
            )
        return {"alias": alias, "shape_key": shape_key, "candidates": candidates, "skipped": skipped}

    def debug_health(self) -> dict[str, Any]:
        now = time.time()
        provider_state = self.state_store.get_provider_state()
        model_state = self.state_store.get_model_state()
        shape_health = self.state_store.get_shape_health()
        shapes: list[dict[str, Any]] = []
        for key, state in shape_health.items():
            provider_name, backend_model, shape_key = key.split("::", 2)
            shapes.append(
                {
                    **state,
                    "health_score": self._shape_health_score(provider_name, backend_model, shape_key),
                    "suppression_active": float(state.get("suppressed_until", 0) or 0) > now,
                    "probe_available": self._shape_probe_available(provider_name, backend_model, shape_key),
                    "suppressed_remaining_seconds": max(0.0, float(state.get("suppressed_until", 0) or 0) - now),
                    "next_probe_in_seconds": max(0.0, float(state.get("next_probe_at", 0) or 0) - now),
                }
            )
        return {
            "providers": list(provider_state.values()),
            "models": list(model_state.values()),
            "shapes": shapes,
        }

    def _render_candidates(self, candidates: list[RouteCandidate]) -> list[dict[str, Any]]:
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

    def _model_is_routable(self, model: ProviderModel, *, alias: str | None = None) -> bool:
        if model.provider != "opencode-go" and not model.is_free:
            return False
        output_modalities = self._output_modalities(model)
        input_modalities = self._input_modalities(model)
        if not self._model_supports_tools(model):
            return False
        if {"image", "video"} & input_modalities:
            return False
        if output_modalities and output_modalities != {"text"}:
            return False
        return True

    def _ranked_model_exclusion_reason(
        self,
        provider_name: str,
        backend_model: str,
        *,
        alias: str,
        model: ProviderModel | None = None,
        shape_key: str = "text",
        requires_tool_protocol: bool = False,
    ) -> str | None:
        resolved_model = model or self._lookup_model(provider_name, backend_model)
        if resolved_model is None:
            return "not_discovered"
        if provider_name != "opencode-go" and not resolved_model.is_free:
            return "not_free"
        if not self._model_supports_tools(resolved_model):
            return "no_tool_support"
        if requires_tool_protocol and not self._model_can_preserve_tool_protocol(resolved_model):
            return "tool_adapter_missing"
        if {"image", "video"} & self._input_modalities(resolved_model):
            return "multimodal_input"
        output_modalities = self._output_modalities(resolved_model)
        if output_modalities and output_modalities != {"text"}:
            return "non_text_output"
        if not self._model_effectively_enabled(provider_name, backend_model):
            return "disabled"
        health_reason = self._rolling_health_suppression_reason(provider_name, backend_model, shape_key=shape_key)
        if health_reason is not None:
            return health_reason
        if self._is_cooling_down(provider_name, backend_model):
            return "model_cooldown"
        if self._provider_is_cooling_down(provider_name):
            return "provider_cooldown"
        if self._provider_is_pacing(provider_name):
            return "provider_pacing"
        return None

    def _model_supports_tools(self, model: ProviderModel) -> bool:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        supported_parameters = metadata.get("supported_parameters")
        if not isinstance(supported_parameters, list):
            return True
        supported = {str(item).strip().lower() for item in supported_parameters if str(item).strip()}
        if not supported:
            return True
        return "tools" in supported or "tool_choice" in supported

    def _model_can_preserve_tool_protocol(self, model: ProviderModel) -> bool:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        endpoint_family = str(metadata.get("endpoint_family") or "chat_completions")
        provider_metadata = metadata.get("provider_metadata")
        advertises_tool_calls = isinstance(provider_metadata, dict) and bool(provider_metadata.get("tool_call"))
        return self._model_supports_tools(model) and (endpoint_family == "chat_completions" or advertises_tool_calls)

    @staticmethod
    def _shape_key_requires_tool_protocol(shape_key: str) -> bool:
        parts = {part for part in shape_key.split("+") if part}
        return bool(parts & {"tools", "tool_history"})

    def _output_modalities(self, model: ProviderModel) -> set[str]:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        output_modalities = metadata.get("output_modalities")
        if not isinstance(output_modalities, list):
            provider_metadata = metadata.get("provider_metadata")
            modalities = provider_metadata.get("modalities") if isinstance(provider_metadata, dict) else None
            output_modalities = modalities.get("output") if isinstance(modalities, dict) else None
        if not isinstance(output_modalities, list):
            return set()
        return {str(item).strip().lower() for item in output_modalities if str(item).strip()}

    def _input_modalities(self, model: ProviderModel) -> set[str]:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        input_modalities = metadata.get("input_modalities")
        if not isinstance(input_modalities, list):
            provider_metadata = metadata.get("provider_metadata")
            modalities = provider_metadata.get("modalities") if isinstance(provider_metadata, dict) else None
            input_modalities = modalities.get("input") if isinstance(modalities, dict) else None
        if not isinstance(input_modalities, list):
            return set()
        return {str(item).strip().lower() for item in input_modalities if str(item).strip()}

    def _model_is_music_audio(self, model: ProviderModel) -> bool:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        haystack = " ".join(
            str(value).lower()
            for value in (
                model.id,
                metadata.get("name"),
                metadata.get("description"),
                metadata.get("modality"),
            )
            if value
        )
        music_tokens = ("lyria", "music", "song", "songs", "lyrics", "stereo", "clip", "instrumental", "vocals")
        return any(token in haystack for token in music_tokens)

    def _resolve_candidates(
        self,
        alias: str,
        *,
        session_id: str | None = None,
        ignore_provider_pacing: bool = False,
        requires_tool_protocol: bool = False,
        shape_key: str = "text",
    ) -> list[RouteCandidate]:
        if alias in {"auxiliary", "coding", "agentic", "vision", "tts"}:
            raise RouterServiceError(404, {"message": f"Logical model alias '{alias}' is retired. Use an exposed OpenCode Go model id."})
        direct_candidates = self._resolve_direct_model(alias)
        if direct_candidates:
            return direct_candidates
        if not self._served_model_is_exposed(alias):
            raise RouterServiceError(404, {"message": f"Unknown or unexposed OpenCode Go model id '{alias}'."})
        candidates = self._served_model_candidates(
            alias,
            ignore_provider_pacing=ignore_provider_pacing,
            advance_round_robin=False,
            requires_tool_protocol=requires_tool_protocol,
            shape_key=shape_key,
        )
        return [
            RouteCandidate(**{**candidate.__dict__, "is_fallback": candidate.provider_name == "opencode-go" or index > 0})
            for index, candidate in enumerate(candidates)
        ]

    def _resolve_remaining_candidates(
        self,
        alias: str,
        attempted: set[tuple[str, str]],
        *,
        session_id: str | None = None,
        ignore_provider_pacing: bool = False,
        requires_tool_protocol: bool = False,
        shape_key: str = "text",
    ) -> list[RouteCandidate]:
        if alias in {"auxiliary", "coding", "agentic", "vision", "tts"}:
            raise RouterServiceError(404, {"message": f"Logical model alias '{alias}' is retired. Use an exposed OpenCode Go model id."})
        if not self._served_model_is_exposed(alias):
            raise RouterServiceError(404, {"message": f"Unknown or unexposed OpenCode Go model id '{alias}'."})
        candidates = self._served_model_candidates(
            alias,
            ignore_provider_pacing=ignore_provider_pacing,
            advance_round_robin=not attempted,
            requires_tool_protocol=requires_tool_protocol,
            shape_key=shape_key,
        )
        available = [
            candidate
            for candidate in candidates
            if (candidate.provider_name, candidate.backend_model) not in attempted
        ]
        return [
            RouteCandidate(**{**candidate.__dict__, "is_fallback": candidate.provider_name == "opencode-go" or index > 0})
            for index, candidate in enumerate(available)
        ]

    def _resolve_direct_model(self, model_name: str) -> list[RouteCandidate]:
        if not self.config.allow_direct_models:
            return []
        return self._preferred_candidates((model_name,), alias=model_name)

    def _served_model_candidates(
        self,
        served_model_id: str,
        *,
        ignore_provider_pacing: bool = False,
        advance_round_robin: bool = False,
        requires_tool_protocol: bool = False,
        shape_key: str = "text",
    ) -> list[RouteCandidate]:
        free_candidates: list[RouteCandidate] = []
        fallback_candidates: list[RouteCandidate] = []
        probe_selected: set[str] = set()
        for model in [*self._free_equivalent_models(served_model_id), *(go_model for go_model in [self._opencode_go_model(served_model_id)] if go_model is not None)]:
            if not self._candidate_is_currently_eligible(
                model,
                ignore_provider_pacing=ignore_provider_pacing,
                probe_selected=probe_selected,
                requires_tool_protocol=requires_tool_protocol,
                shape_key=shape_key,
            ):
                continue
            breakdown = self._candidate_breakdown(served_model_id, model, shape_key=shape_key)
            candidate = RouteCandidate(
                provider_name=model.provider,
                backend_model=model.id,
                total_score=breakdown["total_score"],
                score_breakdown=breakdown,
            )
            target = fallback_candidates if model.provider == "opencode-go" else free_candidates
            if candidate not in target:
                target.append(candidate)
        return [
            *self._round_robin_free_candidates(served_model_id, free_candidates, advance=advance_round_robin, shape_key=shape_key),
            *fallback_candidates,
        ]

    def _candidate_is_currently_eligible(
        self,
        model: ProviderModel,
        *,
        ignore_provider_pacing: bool,
        probe_selected: set[str],
        requires_tool_protocol: bool = False,
        shape_key: str = "text",
    ) -> bool:
        if not self._model_is_routable(model):
            return False
        if requires_tool_protocol and not self._model_can_preserve_tool_protocol(model):
            return False
        if not self._model_effectively_enabled(model.provider, model.id):
            return False
        if model.provider != "opencode-go" and self._rolling_health_suppression_reason(model.provider, model.id, shape_key=shape_key) is not None:
            return False
        if self._provider_is_cooling_down(model.provider):
            return False
        if not ignore_provider_pacing:
            if model.provider != "opencode-go" and self._provider_is_pacing(model.provider):
                return False
            if not self._provider_has_rpm_capacity(model.provider):
                return False
        if self._is_cooling_down(model.provider, model.id):
            return False
        if self._provider_in_probe_mode(model.provider):
            if model.provider in probe_selected:
                return False
            probe_selected.add(model.provider)
        return True

    def _preferred_candidates(
        self,
        model_ids: tuple[str, ...],
        *,
        alias: str | None = None,
        inventory: list[ProviderModel] | None = None,
        ignore_provider_pacing: bool = False,
        advance_round_robin: bool = False,
    ) -> list[RouteCandidate]:
        free_candidates: list[RouteCandidate] = []
        fallback_candidates: list[RouteCandidate] = []
        known_inventory = inventory if inventory is not None else self._inventory_for_all()
        probe_selected: set[str] = set()
        for model_id in model_ids:
            normalized = self._normalize_prefixed_model_id(model_id)
            inferred_provider = self._provider_name_from_prefixed_model_id(model_id)
            if inferred_provider is None:
                matched = [model for model in known_inventory if model.id == normalized or model.id == model_id]
            else:
                matched = [
                    model
                    for model in known_inventory
                    if model.provider == inferred_provider and (model.id == normalized or model.id == model_id)
                ]
            alias_name = alias or normalized
            for model in matched:
                if not self._model_is_routable(model, alias=alias_name):
                    continue
                if not self._model_effectively_enabled(model.provider, model.id):
                    continue
                if model.provider != "opencode-go" and self._rolling_health_suppression_reason(model.provider, model.id) is not None:
                    continue
                if self._provider_is_cooling_down(model.provider):
                    continue
                if not ignore_provider_pacing:
                    if model.provider != "opencode-go" and self._provider_is_pacing(model.provider):
                        continue
                    if not self._provider_has_rpm_capacity(model.provider):
                        continue
                if self._is_cooling_down(model.provider, model.id):
                    continue
                if self._provider_in_probe_mode(model.provider):
                    if model.provider in probe_selected:
                        continue
                    probe_selected.add(model.provider)
                breakdown = self._candidate_breakdown(alias_name, model)
                candidate = RouteCandidate(
                    provider_name=model.provider,
                    backend_model=model.id,
                    total_score=breakdown["total_score"],
                    score_breakdown=breakdown,
                )
                target = fallback_candidates if model.provider == "opencode-go" else free_candidates
                if candidate not in target:
                    target.append(candidate)
        return [
            *self._round_robin_free_candidates(alias or "", free_candidates, advance=advance_round_robin, shape_key="direct"),
            *fallback_candidates,
        ]

    def _round_robin_free_candidates(self, alias: str, candidates: list[RouteCandidate], *, advance: bool, shape_key: str) -> list[RouteCandidate]:
        if len(candidates) <= 1:
            return candidates
        rr_key = f"{alias}:{shape_key}"
        deficits = dict(self._round_robin_deficits)
        remaining = list(candidates)
        selected: list[RouteCandidate] = []
        total_weight = sum(max(1.0, float(candidate.score_breakdown.get("effective_weight", 1.0))) for candidate in remaining)
        provider_order = {provider: index for index, provider in enumerate(self.config.provider_priority)}
        while remaining:
            for candidate in remaining:
                key = f"{rr_key}:{candidate.provider_name}/{candidate.backend_model}"
                deficits[key] = deficits.get(key, 0.0) + max(1.0, float(candidate.score_breakdown.get("effective_weight", 1.0)))
            chosen = max(
                remaining,
                key=lambda candidate: (
                    deficits.get(f"{rr_key}:{candidate.provider_name}/{candidate.backend_model}", 0.0),
                    -provider_order.get(candidate.provider_name, 999),
                ),
            )
            chosen_key = f"{rr_key}:{chosen.provider_name}/{chosen.backend_model}"
            deficits[chosen_key] = deficits.get(chosen_key, 0.0) - max(total_weight, 1.0)
            selected.append(chosen)
            remaining.remove(chosen)
        if advance:
            self._round_robin_deficits = deficits
        return selected

    def _candidate_breakdown(self, alias: str, model: ProviderModel, *, shape_key: str = "text") -> dict[str, Any]:
        state = self._candidate_state(model.provider, model.id, shape_key=shape_key)
        health_score = self._shape_health_score(model.provider, model.id, shape_key)
        base_weight = max(1, self._provider_rpm_limit(model.provider) or 1)
        effective_weight = max(1.0, round(base_weight * health_score, 2))
        return {
            "model": alias,
            "total_score": effective_weight,
            "shape_key": shape_key,
            "health_score": health_score,
            "effective_weight": effective_weight,
            "rpm": self._provider_rpm_state(model.provider),
            "cooldown_until": state["model_cooldown_until"],
            "provider_cooldown_until": state["provider_cooldown_until"],
            "provider_next_request_at": state["provider_next_request_at"],
            "last_latency_ms": state["last_latency_ms"],
            "last_first_text_latency_ms": state["last_first_text_latency_ms"],
            "recent_provider_timeout": state["recent_provider_timeout"],
            "recent_model_timeout": state["recent_model_timeout"],
            "timeout_guard_active": state["timeout_guard_active"],
            "timeout_guard_until": state["timeout_guard_until"],
            "recent_provider_first_text_latency_ms": state["recent_provider_first_text_latency_ms"],
            "recent_model_first_text_latency_ms": state["recent_model_first_text_latency_ms"],
            "recent_provider_latency_ms": state["recent_provider_latency_ms"],
            "recent_model_latency_ms": state["recent_model_latency_ms"],
            "slow_guard_active": state["slow_guard_active"],
            "slow_guard_until": state["slow_guard_until"],
        }

    def _shape_health_key(self, provider_name: str, backend_model: str, shape_key: str) -> str:
        return f"{provider_name}::{backend_model}::{shape_key}"

    def _shape_health(self, provider_name: str, backend_model: str, shape_key: str) -> dict[str, Any]:
        return self.state_store.get_shape_health().get(self._shape_health_key(provider_name, backend_model, shape_key), {})

    def _shape_health_score(self, provider_name: str, backend_model: str, shape_key: str) -> float:
        if provider_name == "opencode-go":
            return 1.0
        state = self._shape_health(provider_name, backend_model, shape_key)
        recent_timeout = self._decayed_state_value(state, "recent_timeout")
        recent_failure = self._decayed_state_value(state, "recent_failure")
        recent_slow = self._decayed_state_value(state, "recent_slow_success")
        level = int(state.get("suppression_level", 0) or 0)
        score = 1.0 / (1.0 + (recent_timeout * 3.0) + recent_failure + (recent_slow * 0.75) + level)
        if self._shape_probe_available(provider_name, backend_model, shape_key):
            score = min(score, 0.1)
        return round(max(0.05, min(1.0, score)), 4)

    def _shape_probe_available(self, provider_name: str, backend_model: str, shape_key: str) -> bool:
        state = self._shape_health(provider_name, backend_model, shape_key)
        if provider_name == "opencode-go" or not state:
            return False
        now = time.time()
        return float(state.get("suppressed_until", 0) or 0) > now and float(state.get("next_probe_at", 0) or 0) <= now

    def _shape_suppression_reason(self, provider_name: str, backend_model: str, shape_key: str) -> str | None:
        if provider_name == "opencode-go":
            return None
        state = self._shape_health(provider_name, backend_model, shape_key)
        if not state:
            return None
        now = time.time()
        if float(state.get("suppressed_until", 0) or 0) > now and float(state.get("next_probe_at", 0) or 0) > now:
            return "shape_suppressed"
        return None

    def _rolling_health_suppression_reason(self, provider_name: str, backend_model: str, *, shape_key: str = "text") -> str | None:
        return (
            self._shape_suppression_reason(provider_name, backend_model, shape_key)
            or self._rolling_timeout_suppression_reason(provider_name, backend_model)
            or self._rolling_slow_suppression_reason(provider_name, backend_model)
        )

    def _rolling_timeout_suppression_reason(self, provider_name: str, backend_model: str) -> str | None:
        if provider_name == "opencode-go":
            return None
        threshold = float(self.config.provider_timeout_threshold)
        if threshold <= 0:
            return None
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        if self._decayed_state_value(provider_state, "recent_timeout") >= threshold:
            return "provider_timeout_guard"
        model_state = self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        if self._decayed_state_value(model_state, "recent_timeout") >= threshold:
            return "model_timeout_guard"
        return None

    def _rolling_slow_suppression_reason(self, provider_name: str, backend_model: str) -> str | None:
        if provider_name == "opencode-go":
            return None
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        model_state = self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        first_text_threshold = float(self.config.provider_slow_first_text_threshold_ms)
        if first_text_threshold > 0:
            if self._decayed_state_value(provider_state, "first_text_latency_avg_ms") >= first_text_threshold:
                return "provider_slow_first_text_guard"
            if self._decayed_state_value(model_state, "first_text_latency_avg_ms") >= first_text_threshold:
                return "model_slow_first_text_guard"
        total_threshold = float(self.config.provider_slow_total_threshold_ms)
        if total_threshold > 0:
            if self._decayed_state_value(provider_state, "latency_avg_ms") >= total_threshold:
                return "provider_slow_latency_guard"
            if self._decayed_state_value(model_state, "latency_avg_ms") >= total_threshold:
                return "model_slow_latency_guard"
        return None

    def _candidate_state(self, provider_name: str, backend_model: str, *, shape_key: str = "text") -> dict[str, Any]:
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        model_state = self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        shape_state = self._shape_health(provider_name, backend_model, shape_key)
        return {
            "provider_cooldown_until": provider_state.get("cooldown_until", 0),
            "model_cooldown_until": model_state.get("cooldown_until", 0),
            "provider_next_request_at": provider_state.get("next_request_at", 0),
            "last_latency_ms": provider_state.get("last_latency_ms"),
            "last_first_text_latency_ms": provider_state.get("last_first_text_latency_ms"),
            "recent_provider_timeout": self._decayed_state_value(provider_state, "recent_timeout"),
            "recent_model_timeout": self._decayed_state_value(model_state, "recent_timeout"),
            "timeout_guard_active": self._rolling_timeout_suppression_reason(provider_name, backend_model) is not None,
            "timeout_guard_until": self._timeout_guard_until(provider_name, backend_model),
            "recent_provider_first_text_latency_ms": self._decayed_state_value(provider_state, "first_text_latency_avg_ms"),
            "recent_model_first_text_latency_ms": self._decayed_state_value(model_state, "first_text_latency_avg_ms"),
            "recent_provider_latency_ms": self._decayed_state_value(provider_state, "latency_avg_ms"),
            "recent_model_latency_ms": self._decayed_state_value(model_state, "latency_avg_ms"),
            "slow_guard_active": self._rolling_slow_suppression_reason(provider_name, backend_model) is not None,
            "slow_guard_until": self._slow_guard_until(provider_name, backend_model),
            "shape_key": shape_key,
            "shape_health": shape_state,
            "shape_health_score": self._shape_health_score(provider_name, backend_model, shape_key),
            "shape_suppression_reason": self._shape_suppression_reason(provider_name, backend_model, shape_key),
            "shape_probe_available": self._shape_probe_available(provider_name, backend_model, shape_key),
            "rpm": self._provider_rpm_state(provider_name),
        }

    def _timeout_guard_until(self, provider_name: str, backend_model: str) -> float | None:
        if provider_name == "opencode-go":
            return None
        threshold = float(self.config.provider_timeout_threshold)
        if threshold <= 0:
            return None
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        model_state = self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        waits = [
            self._decay_wait_until_below_threshold(provider_state, "recent_timeout", threshold),
            self._decay_wait_until_below_threshold(model_state, "recent_timeout", threshold),
        ]
        active_waits = [value for value in waits if value is not None]
        return max(active_waits) if active_waits else None

    def _slow_guard_until(self, provider_name: str, backend_model: str) -> float | None:
        if provider_name == "opencode-go":
            return None
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        model_state = self.state_store.get_model_state().get(self._model_key(provider_name, backend_model), {})
        waits: list[float | None] = []
        first_text_threshold = float(self.config.provider_slow_first_text_threshold_ms)
        if first_text_threshold > 0:
            waits.extend(
                [
                    self._decay_wait_until_below_threshold(provider_state, "first_text_latency_avg_ms", first_text_threshold),
                    self._decay_wait_until_below_threshold(model_state, "first_text_latency_avg_ms", first_text_threshold),
                ]
            )
        total_threshold = float(self.config.provider_slow_total_threshold_ms)
        if total_threshold > 0:
            waits.extend(
                [
                    self._decay_wait_until_below_threshold(provider_state, "latency_avg_ms", total_threshold),
                    self._decay_wait_until_below_threshold(model_state, "latency_avg_ms", total_threshold),
                ]
            )
        active_waits = [value for value in waits if value is not None]
        return max(active_waits) if active_waits else None

    def _decayed_state_value(self, state: dict[str, Any], key: str) -> float:
        try:
            value = float(state.get(key, 0) or 0)
            updated_at = float(state.get("updated_at", 0) or 0)
        except (TypeError, ValueError):
            return 0.0
        if value <= 0 or updated_at <= 0:
            return max(value, 0.0)
        elapsed = max(0.0, time.time() - updated_at)
        return round(value * math.exp(-elapsed / self.config.rolling_window_seconds), 6)

    def _decay_wait_until_below_threshold(self, state: dict[str, Any], key: str, threshold: float) -> float | None:
        try:
            value = float(state.get(key, 0) or 0)
            updated_at = float(state.get("updated_at", 0) or 0)
        except (TypeError, ValueError):
            return None
        decayed = self._decayed_state_value(state, key)
        if value <= 0 or updated_at <= 0 or decayed < threshold:
            return None
        seconds = self.config.rolling_window_seconds * math.log(decayed / threshold)
        return time.time() + max(0.0, seconds)

    def _provider_order(self, *, session_id: str | None = None) -> tuple[str, ...]:
        ordered = [name for name in self.config.provider_priority if name in self.providers]
        affinity = self._session_affinity.get(session_id or "")
        sticky_provider = str(affinity.get("provider_name") or "") if affinity else ""
        if sticky_provider and sticky_provider in ordered and self._provider_enabled(sticky_provider):
            ordered = [sticky_provider, *(name for name in ordered if name != sticky_provider)]
        return tuple(ordered)

    def _remember_session_affinity(self, session_id: str | None, candidate: RouteCandidate) -> None:
        if not session_id:
            return
        self._session_affinity[session_id] = {
            "provider_name": candidate.provider_name,
            "backend_model": candidate.backend_model,
            "updated_at": time.time(),
        }

    def _inventory_for_all(self) -> list[ProviderModel]:
        return list(self._inventory)

    def _opencode_go_models(self, *, inventory: list[ProviderModel] | None = None) -> list[ProviderModel]:
        models = [
            model
            for model in (inventory if inventory is not None else self._inventory_for_all())
            if model.provider == "opencode-go" and self._model_is_routable(model) and self._model_effectively_enabled(model.provider, model.id)
        ]
        return sorted(models, key=lambda item: item.id)

    def _opencode_go_model(self, served_model_id: str, *, inventory: list[ProviderModel] | None = None) -> ProviderModel | None:
        for model in self._opencode_go_models(inventory=inventory):
            if model.id == served_model_id:
                return model
        return None

    def _free_equivalent_models(self, served_model_id: str, *, inventory: list[ProviderModel] | None = None) -> list[ProviderModel]:
        known_inventory = inventory if inventory is not None else self._inventory_for_all()
        if self._opencode_go_model(served_model_id, inventory=known_inventory) is None:
            return []
        target_key = self._canonical_model_key(served_model_id)
        matches: list[ProviderModel] = []
        for provider_name in self.config.provider_priority:
            if provider_name == "opencode-go" or provider_name not in self.providers:
                continue
            for model in known_inventory:
                if model.provider != provider_name:
                    continue
                if not model.is_free:
                    continue
                if self._canonical_model_key(model.id) != target_key:
                    continue
                if not self._model_is_routable(model):
                    continue
                if model not in matches:
                    matches.append(model)
        return matches

    def _served_model_is_exposed(self, served_model_id: str) -> bool:
        return self._opencode_go_model(served_model_id) is not None and bool(self._free_equivalent_models(served_model_id))

    @staticmethod
    def _canonical_model_key(model_id: str) -> str:
        lowered = model_id.strip().lower()
        tail = lowered.rsplit("/", 1)[-1]
        for suffix in (":free", "-free"):
            if tail.endswith(suffix):
                tail = tail[: -len(suffix)]
        return "".join(char for char in tail if char.isalnum())

    def _seeded_backend_ids_for_provider(self, provider_name: str) -> set[str]:
        seeded: set[str] = set()
        policy = self.config.provider_seed_map().get(provider_name)
        if policy is not None:
            seeded.update(policy.seeded_models)
        return seeded

    def _model_allowed(self, model_id: str) -> bool:
        normalized = self._normalize_prefixed_model_id(model_id)
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

    def _provider_is_pacing(self, provider_name: str, *, state: dict[str, Any] | None = None) -> bool:
        provider_state = state or self.state_store.get_provider_state().get(provider_name, {})
        return float(provider_state.get("next_request_at", 0) or 0) > time.time()

    def _provider_spacing_seconds(self, provider_name: str) -> float:
        if self._provider_rpm_limit(provider_name) is not None:
            return 0.0
        if provider_name == "nvidia-build":
            return self.config.nvidia_build_min_request_spacing_seconds
        if provider_name == "openrouter":
            return self.config.openrouter_min_request_spacing_seconds
        if provider_name == "opencode-zen":
            return self.config.opencode_min_request_spacing_seconds
        if provider_name == "opencode-go":
            return self.config.opencode_min_request_spacing_seconds
        return min(
            self.config.nvidia_build_min_request_spacing_seconds,
            self.config.openrouter_min_request_spacing_seconds,
            self.config.opencode_min_request_spacing_seconds,
        )

    def _provider_rpm_limit(self, provider_name: str) -> int | None:
        if provider_name == "opencode-go":
            return None
        value = self.config.provider_rpm_limits.get(provider_name)
        if value is None or int(value) <= 0:
            return None
        return int(value)

    def _provider_rpm_used(self, provider_name: str) -> int:
        return self.state_store.count_provider_requests_since(provider_name, time.time() - 60.0)

    def _provider_has_rpm_capacity(self, provider_name: str) -> bool:
        limit = self._provider_rpm_limit(provider_name)
        if limit is None:
            return True
        return self._provider_rpm_used(provider_name) < limit

    def _provider_rpm_state(self, provider_name: str) -> dict[str, Any]:
        limit = self._provider_rpm_limit(provider_name)
        used = self._provider_rpm_used(provider_name)
        return {
            "configured": provider_name in self.providers,
            "enabled": self._provider_enabled(provider_name),
            "rpm_limit": limit,
            "used_60s": used,
            "remaining_60s": None if limit is None else max(limit - used, 0),
            "available": self._provider_enabled(provider_name)
            and not self._provider_is_cooling_down(provider_name)
            and not self._provider_is_pacing(provider_name)
            and self._provider_has_rpm_capacity(provider_name),
        }

    def _provider_suppression_source(self, provider_name: str, *, state: dict[str, Any] | None = None) -> str | None:
        provider_state = state or self.state_store.get_provider_state().get(provider_name, {})
        if self._provider_is_cooling_down(provider_name, state=provider_state):
            return "hard_provider_disable"
        if self._provider_is_pacing(provider_name, state=provider_state):
            return "provider_pacing"
        if self._provider_in_probe_mode(provider_name, state=provider_state):
            return "probe_mode"
        return None

    def _provider_retry_after_seconds(self, details: Any) -> float | None:
        if not isinstance(details, dict):
            return None
        raw = details.get("retry_after_seconds")
        if raw is None:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    @staticmethod
    def _is_temporary_provider_throttle(details: Any) -> bool:
        return isinstance(details, dict) and bool(details.get("temporary_throttle") or details.get("provider_pacing") or details.get("retry_after_seconds"))

    def _provider_throttle_until(self, provider_name: str, exc: NormalizedProviderError) -> float | None:
        if exc.category != "rate_limited" or not self._is_temporary_provider_throttle(exc.details):
            return None
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        ladder = self.config.provider_throttle_ladder_seconds or (15,)
        streak = int(provider_state.get("throttle_streak", 0) or 0)
        index = min(streak, len(ladder) - 1)
        delay_seconds = float(ladder[index])
        retry_after_seconds = self._provider_retry_after_seconds(exc.details)
        if retry_after_seconds is not None:
            delay_seconds = max(delay_seconds, retry_after_seconds)
        delay_seconds = max(delay_seconds, self._provider_spacing_seconds(provider_name))
        return time.time() + delay_seconds

    @staticmethod
    def _should_apply_model_cooldown(exc: NormalizedProviderError) -> bool:
        if exc.category in {"timeout", "connect_timeout", "first_byte_timeout", "read_timeout", "request_timeout"}:
            return False
        if exc.category in {"quota_exhausted", "insufficient_balance"}:
            return isinstance(exc.details, dict) and bool(exc.details.get("model_scoped"))
        if exc.category in {"bad_request", "tool_choice_unsupported"}:
            return False
        if exc.category == "rate_limited":
            return not RouterService._is_temporary_provider_throttle(exc.details)
        return True

    def _paced_wait_seconds(
        self,
        alias: str,
        attempted: set[tuple[str, str]],
        *,
        session_id: str | None = None,
        requires_tool_protocol: bool = False,
    ) -> float | None:
        provider_state = self.state_store.get_provider_state()
        max_wait_seconds = max(
            self.config.nvidia_build_min_request_spacing_seconds,
            self.config.openrouter_min_request_spacing_seconds,
            self.config.opencode_min_request_spacing_seconds,
        )
        waits: list[float] = []
        for candidate in self._resolve_candidates(
            alias,
            session_id=session_id,
            ignore_provider_pacing=True,
            requires_tool_protocol=requires_tool_protocol,
        ):
            if (candidate.provider_name, candidate.backend_model) in attempted:
                continue
            state = provider_state.get(candidate.provider_name, {})
            if self._provider_is_cooling_down(candidate.provider_name, state=state):
                continue
            if not self._provider_is_pacing(candidate.provider_name, state=state):
                continue
            wait_seconds = float(state.get("next_request_at", 0) or 0) - time.time()
            if wait_seconds > 0:
                waits.append(wait_seconds)
        if not waits:
            return None
        soonest = min(waits)
        if soonest > max_wait_seconds:
            return None
        return soonest

    def _provider_in_probe_mode(self, provider_name: str, *, state: dict[str, Any] | None = None) -> bool:
        provider_state = state or self.state_store.get_provider_state().get(provider_name, {})
        now = time.time()
        if float(provider_state.get("cooldown_until", 0) or 0) > now:
            return False
        if not int(provider_state.get("breaker_level", 0) or 0):
            return False
        if int(provider_state.get("probe_mode", 0) or 0):
            return True
        self.state_store.activate_provider_probe(provider_name)
        provider_state = self.state_store.get_provider_state().get(provider_name, {})
        return bool(int(provider_state.get("probe_mode", 0) or 0))

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
        recent_auth_failure = float(provider_state.get("recent_auth_failure", 0) or 0)
        recent_success = float(provider_state.get("recent_success", 0) or 0)
        if recent_auth_failure >= 1.0 and recent_success < 0.1:
            category = "unauthorized"
        elif float(provider_state.get("recent_timeout", 0)) >= self.config.provider_timeout_threshold:
            category = "timeout"
        elif float(provider_state.get("recent_server_error", 0)) >= self.config.provider_failure_threshold:
            category = "server_error"
        if category is None:
            return
        self.state_store.set_provider_cooldown(
            provider_name,
            cooldown_until=now + self.config.provider_cooldown_seconds,
            category=category,
            details={"source": "provider_guard"},
        )

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

    @staticmethod
    def _provider_name_from_prefixed_model_id(model_id: str) -> str | None:
        prefixes = {
            "opencode/": "opencode-zen",
            "opencode-zen/": "opencode-zen",
            "opencode-go/": "opencode-go",
            "openrouter/": "openrouter",
            "nvidia/": "nvidia-build",
            "nvidia-build/": "nvidia-build",
            "zenmux/": "zenmux",
            "electron-hub/": "electron-hub",
        }
        lowered = model_id.lower()
        for prefix, provider_name in prefixes.items():
            if lowered.startswith(prefix):
                return provider_name
        return None

    @classmethod
    def _normalize_prefixed_model_id(cls, model_id: str) -> str:
        provider_name = cls._provider_name_from_prefixed_model_id(model_id)
        if provider_name is None:
            return model_id
        prefix = "nvidia-build/" if model_id.lower().startswith("nvidia-build/") else f"{model_id.split('/', 1)[0]}/"
        return model_id.removeprefix(prefix)

    def _log_event(self, event: str, **fields: Any) -> None:
        logger.info("router_event %s", json.dumps({"event": event, **fields}, sort_keys=True))
