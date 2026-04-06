from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from typing import Any

from .config import AliasConfig, RouterConfig
from .models import ChatCompletionRequest, ModelCard, ModelsResponse, ReadinessResponse, ResponsesRequest
from .providers.base import ChatProvider, NormalizedProviderError, ProviderChatStreamEvent, ProviderChatStreamResult, ProviderModel
from .providers.opencode_zen import OpencodeZenProvider
from .providers.openrouter import OpenRouterProvider
from .state import RouteEvent, SqliteStateStore, StateStore

logger = logging.getLogger("hermes_router")

_ALIASES = ("auxiliary", "coding", "agentic", "vision", "tts")

_ALIAS_HINTS: dict[str, tuple[str, ...]] = {
    "auxiliary": ("mini", "small", "flash", "flash-lite", "nano", "haiku"),
    "coding": ("coder", "coding", "code", "codex", "qwen", "deepseek", "devstral", "reason", "thinking", "opus", "sonnet", "large", "70b", "72b", "swe"),
    "agentic": ("agent", "tool", "operator", "orchestr", "swe", "reason", "thinking", "sonnet", "opus", "grok", "glm", "minimax"),
    "vision": ("vision", "vl", "image", "video", "multimodal", "omni", "5v", "gemma-4"),
    "tts": ("audio", "speech", "voice", "tts", "narration"),
}

_ALIAS_PENALTIES: dict[str, tuple[str, ...]] = {
    "auxiliary": ("large", "70b", "72b", "reason", "thinking", "vision", "video", "audio"),
    "coding": ("audio", "speech", "tts", "music"),
    "agentic": ("audio", "speech", "tts", "music"),
    "vision": ("audio", "speech", "tts", "music"),
    "tts": ("vision", "image", "video", "music", "song", "lyrics", "lyria"),
}

_FAMILY_PRIORS_BY_ALIAS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "coding": (
        ("minimax", ("minimax", "m2.7", "m2.5")),
        ("glm", ("glm-5", "glm", "z.ai", "z-ai")),
        ("qwen", ("qwen3-coder-next", "qwen3.6-plus", "qwen3.6", "qwen3-coder", "qwen")),
        ("deepseek", ("deepseek", "speciale")),
        ("grok", ("grok code fast", "grok-code-fast", "grok 4.1 fast", "grok")),
        ("gemini", ("gemini-3-flash", "gemini-3.1-pro", "gemini-3-pro", "gemini")),
        ("stepfun", ("step-3.5", "stepfun", "step-")),
        ("devstral", ("devstral", "mistral")),
        ("nemotron", ("nemotron",)),
        ("mimo", ("mimo-v2", "mimo")),
        ("trinity", ("trinity", "arcee", "arcee-ai")),
        ("gpt-oss", ("gpt-oss",)),
        ("olmo", ("olmo",)),
        ("gemma", ("gemma",)),
        ("hermes", ("hermes",)),
        ("solar", ("solar",)),
        ("llama", ("llama",)),
        ("venice", ("venice",)),
        ("lfm", ("lfm", "liquid/lfm", "lfm2")),
        ("molmo", ("molmo",)),
    ),
    "agentic": (
        ("gemini", ("gemini-3.1-pro", "gemini-3-pro", "gemini")),
        ("trinity", ("trinity", "arcee", "arcee-ai")),
        ("minimax", ("minimax", "m2.7", "m2.5")),
        ("qwen", ("qwen3.6-plus", "qwen3.6", "qwen3-coder", "qwen")),
        ("mimo", ("mimo-v2", "mimo")),
        ("nemotron", ("nemotron",)),
        ("glm", ("glm-5", "glm", "z.ai", "z-ai")),
        ("stepfun", ("step-3.5", "stepfun", "step-")),
        ("deepseek", ("deepseek", "speciale")),
        ("grok", ("grok code fast", "grok-code-fast", "grok 4.1 fast", "grok")),
        ("devstral", ("devstral", "mistral")),
        ("gpt-oss", ("gpt-oss",)),
    ),
    "vision": (
        ("gemma", ("gemma",)),
        ("qwen", ("qwen",)),
        ("nemotron", ("nemotron",)),
        ("molmo", ("molmo",)),
        ("llama", ("llama",)),
    ),
    "auxiliary": (
        ("gemini", ("gemini flash-lite", "gemini flash", "gemini-3.1-flash-lite", "gemini-3-flash", "gemini")),
        ("gpt-oss", ("gpt-oss",)),
        ("nemotron", ("nemotron",)),
        ("mimo", ("mimo-v2-flash", "mimo-v2", "mimo")),
        ("grok", ("grok code fast", "grok-code-fast", "grok fast", "grok")),
        ("stepfun", ("step-3.5", "stepfun", "step-")),
        ("glm", ("glm-5 turbo", "glm-5", "glm", "z.ai", "z-ai")),
        ("minimax", ("minimax", "m2.7-highspeed", "m2.7", "m2.5")),
        ("lfm", ("lfm", "liquid/lfm", "lfm2")),
        ("gemma", ("gemma",)),
    ),
}

_FAMILY_RANK_STEP_BY_ALIAS: dict[str, float] = {
    "coding": 7.0,
    "agentic": 6.0,
    "auxiliary": 3.0,
    "vision": 0.0,
    "tts": 0.0,
}

_SIZE_HINTS: tuple[tuple[str, float], ...] = (
    ("nano", -3.0),
    ("mini", -2.5),
    ("small", -2.0),
    ("lite", -1.5),
    ("flash", -1.0),
    ("air", -0.75),
    ("turbo", -0.5),
    ("plus", 0.25),
    ("pro", 1.0),
    ("large", 1.5),
    ("super", 1.5),
    ("max", 2.0),
    ("ultra", 2.0),
    ("reason", 0.75),
    ("thinking", 0.75),
)


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
class PreparedResponsesRequest:
    chat_request: ChatCompletionRequest
    instructions: str | None
    conversation_history: list[dict[str, Any]]
    previous_response_id: str | None
    request: ResponsesRequest


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
        if not self._inventory:
            return ReadinessResponse(ok=False, providers=sorted(self.providers.keys()), detail="Router inventory is still loading.")
        return ReadinessResponse(ok=True, providers=sorted(self.providers.keys()), detail="Router is ready.")

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
        candidate, stream_result, first_chunk, chunk_iter = self._open_chat_stream(request_for_routing)
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
                self._record_failure(candidate, request_for_routing.model, exc, latency_ms=round((time.monotonic() - started_at) * 1000, 2), is_fallback=candidate.is_fallback)
                raise
            latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            first_text_latency_ms = stream_result.state.first_text_latency_ms or latency_ms
            final_payload = stream_result.state.final_payload or self._chat_payload_from_stream_state(
                request_for_routing.model,
                stream_result.backend_model,
                stream_result.state,
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
        candidate, stream_result, first_chunk, chunk_iter = self._open_chat_stream(prepared.chat_request)
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
            self.state_store.apply_success(
                candidate.provider_name,
                candidate.backend_model,
                latency_ms=latency_ms,
                first_text_latency_ms=first_text_latency_ms,
            )
            self._apply_provider_health_guards(candidate.provider_name)
            self.state_store.record_attempt(
                RouteEvent(
                    alias=prepared.chat_request.model,
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

    def _open_chat_stream(
        self,
        request: ChatCompletionRequest,
    ) -> tuple[RouteCandidate, ProviderChatStreamResult, ProviderChatStreamEvent | None, Iterator[ProviderChatStreamEvent]]:
        candidates = self._resolve_candidates(request.model)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request.model}'."})

        request_payload = request.model_dump(mode="json", exclude_none=True)
        request_payload.pop("timeout", None)
        attempt_errors: list[dict[str, Any]] = []
        for index, candidate in enumerate(candidates):
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                continue
            try:
                stream_result = provider.chat_completions_stream(
                    candidate.backend_model,
                    request_payload,
                    timeout=request.timeout or self.config.default_timeout,
                )
                chunk_iter = iter(stream_result.chunks)
                try:
                    first_chunk = next(chunk_iter)
                except StopIteration:
                    first_chunk = None
                return candidate, stream_result, first_chunk, chunk_iter
            except NormalizedProviderError as exc:
                self._record_failure(candidate, request.model, exc, latency_ms=None, is_fallback=(index > 0))
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
        raise RouterServiceError(503, {"message": f"All route candidates failed for alias '{request.model}'.", "attempts": attempt_errors})

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
        messages.append(self._chat_message_from_payload(payload))
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
            if not self._model_is_routable(model, alias=alias):
                continue
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
                if not self._model_is_routable(model, alias=alias):
                    continue
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


    def _model_is_routable(self, model: ProviderModel, *, alias: str | None = None) -> bool:
        if not model.is_free:
            return False
        output_modalities = self._output_modalities(model)
        input_modalities = self._input_modalities(model)
        if alias == "tts":
            return "audio" in output_modalities and not self._model_is_music_audio(model)
        if alias == "vision":
            if not ({"image", "video"} & input_modalities):
                return False
            return not output_modalities or output_modalities == {"text"}
        if alias == "agentic":
            if not self._model_supports_tools(model):
                return False
            return not output_modalities or output_modalities == {"text"}
        if not self._model_supports_tools(model):
            return False
        if output_modalities and output_modalities != {"text"}:
            return False
        return True

    def _model_supports_tools(self, model: ProviderModel) -> bool:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        supported_parameters = metadata.get("supported_parameters")
        if not isinstance(supported_parameters, list):
            return True
        supported = {str(item).strip().lower() for item in supported_parameters if str(item).strip()}
        if not supported:
            return True
        return "tools" in supported or "tool_choice" in supported

    def _output_modalities(self, model: ProviderModel) -> set[str]:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        output_modalities = metadata.get("output_modalities")
        if not isinstance(output_modalities, list):
            return set()
        return {str(item).strip().lower() for item in output_modalities if str(item).strip()}

    def _input_modalities(self, model: ProviderModel) -> set[str]:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        input_modalities = metadata.get("input_modalities")
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

    def _resolve_candidates(self, alias: str) -> list[RouteCandidate]:
        alias_config = self.config.alias_map().get(alias)
        if alias_config is None:
            direct_candidates = self._resolve_direct_model(alias)
            if direct_candidates:
                return direct_candidates
            raise RouterServiceError(404, {"message": f"Unknown logical model alias '{alias}'."})

        pinned_models = self._alias_pins(alias, alias_config)
        candidates = self._preferred_candidates(pinned_models, alias=alias)
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
        return self._preferred_candidates((model_name,), alias=self._alias_for_model_id(model_name))

    def _preferred_candidates(self, model_ids: tuple[str, ...], *, alias: str | None = None, inventory: list[ProviderModel] | None = None) -> list[RouteCandidate]:
        candidates: list[RouteCandidate] = []
        known_inventory = inventory if inventory is not None else self._inventory_for_all()
        for model_id in model_ids:
            normalized = model_id
            if normalized.startswith("opencode/"):
                normalized = normalized.removeprefix("opencode/")
            elif normalized.startswith("openrouter/"):
                normalized = normalized.removeprefix("openrouter/")
            matched = [model for model in known_inventory if model.id == normalized or model.id == model_id]
            if known_inventory and not matched and normalized == model_id and "openrouter" in self.providers:
                matched.append(ProviderModel(id=model_id, provider="openrouter", is_free=model_id.endswith(":free")))
            elif known_inventory and not matched and normalized != model_id and "openrouter" in self.providers:
                matched.append(ProviderModel(id=normalized, provider="openrouter", is_free=normalized.endswith(":free")))
            alias_name = alias or self._alias_for_model_id(model_id) or "coding"
            for model in matched:
                if not self._model_is_routable(model, alias=alias_name):
                    continue
                if not self._model_effectively_enabled(model.provider, model.id):
                    continue
                if self._provider_is_cooling_down(model.provider):
                    continue
                if self._is_cooling_down(model.provider, model.id):
                    continue
                breakdown = self._score_breakdown(alias_name, model)
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
            if self._model_is_routable(model, alias=alias.name)
            and self._model_effectively_enabled(model.provider, model.id)
            and not self._is_cooling_down(model.provider, model.id)
            and not self._provider_is_cooling_down(model.provider)
        ]
        scored = sorted(filtered, key=lambda model: self._score_breakdown(alias.name, model)["total_score"], reverse=True)
        selected: list[ProviderModel] = []
        selected_keys: set[tuple[str, str]] = set()

        def append_candidates(models: list[ProviderModel]) -> None:
            for model in models:
                if self._score_breakdown(alias.name, model)["total_score"] <= 0:
                    continue
                key = (model.provider, model.id)
                if key in selected_keys:
                    continue
                selected.append(model)
                selected_keys.add(key)
                if len(selected) >= self.config.alias_model_limit:
                    return

        primary = [model for model in scored if self._primary_alias_for_model(model) == alias.name]
        append_candidates(primary)
        if len(selected) < self.config.alias_model_limit:
            append_candidates(scored)
        return selected

    def _inventory_for_all(self) -> list[ProviderModel]:
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
                hint_score += 0.75
        for token in model.tags:
            if token == alias:
                hint_score += 0.5
        for token in _ALIAS_PENALTIES.get(alias, ()):
            if token in lowered:
                penalty_score -= 1.0
        free_score = 100.0 if model.is_free else 0.0
        provider_bias = 0.25 if model.provider == "openrouter" else 0.0
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
        family_name, family_bias = self._family_bias(alias, model)
        parameter_count_b, parameter_bias = self._parameter_bias(alias, model, family_name=family_name)
        created_bias = self._recency_bias(model)
        alias_scores = ranking.get("alias_scores", {})
        rerank_scores = ranking.get("rerank_scores", {})
        learned_score = (float(alias_scores.get(alias, 0.0)) * 3.0) + (float(rerank_scores.get(alias, 0.0)) * 2.0)
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
            + family_bias
            + parameter_bias
            + created_bias
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
            "family_bias": round(family_bias, 3),
            "family_name": family_name,
            "parameter_count_b": parameter_count_b,
            "parameter_bias": round(parameter_bias, 3),
            "recency_bias": round(created_bias, 3),
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
        workers = self._select_ranking_workers(models)
        if not workers:
            self._last_ranking_error = {"message": "No healthy free auxiliary ranking worker available."}
            self._last_ranking_worker = None
            self._last_bucket_model = None
            return
        last_error: dict[str, Any] | None = None
        for worker in workers:
            provider = self.providers.get(worker.provider_name)
            if provider is None:
                continue
            try:
                classifications, rankings = self._rank_inventory_with_worker(provider, worker.backend_model, models)
            except NormalizedProviderError as exc:
                last_error = {"category": exc.category, "details": exc.details}
                self._last_ranking_worker = {"provider_name": worker.provider_name, "backend_model": worker.backend_model}
                self._last_bucket_model = None
                self._log_event("ranking_failed", provider=worker.provider_name, backend_model=worker.backend_model, category=exc.category)
                continue
            if classifications:
                self.state_store.save_classifications(classifications, source=worker.backend_model)
            if rankings:
                self.state_store.save_rankings(
                    rankings,
                    source="auxiliary-free-worker",
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
            return
        self._last_ranking_error = last_error
        self._last_bucket_model = None

    def _select_ranking_workers(self, models: list[ProviderModel]) -> list[RouteCandidate]:
        override_model = self.config.ranking_worker_model or self.config.assisted_bucket_model
        if override_model:
            forced = self._preferred_candidates((override_model,), inventory=models)
            return [item for item in forced if self._model_is_free(item.provider_name, item.backend_model, inventory=models)]
        if self.config.alias_map().get("auxiliary") is None:
            return []

        def sorted_candidates(preferred_provider: str | None = None) -> list[RouteCandidate]:
            candidates: list[RouteCandidate] = []
            for model in models:
                if preferred_provider is not None and model.provider != preferred_provider:
                    continue
                if not self._model_is_routable(model, alias="auxiliary"):
                    continue
                if not self._model_effectively_enabled(model.provider, model.id):
                    continue
                if self._provider_is_cooling_down(model.provider):
                    continue
                if self._is_cooling_down(model.provider, model.id):
                    continue
                breakdown = self._score_breakdown("auxiliary", model)
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
            return sorted(candidates, key=lambda item: item.total_score, reverse=True)

        ordered: list[RouteCandidate] = []
        seen: set[tuple[str, str]] = set()
        for provider_name in ("opencode-zen", "openrouter", None):
            for candidate in sorted_candidates(provider_name):
                key = (candidate.provider_name, candidate.backend_model)
                if key in seen:
                    continue
                ordered.append(candidate)
                seen.add(key)
        return ordered

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
                            "{\"models\": [{\"provider\": \"...\", \"id\": \"...\", \"tags\": [\"coding\"], "
                            "\"alias_scores\": {\"auxiliary\": 0-12, \"coding\": 0-12, \"agentic\": 0-12, \"vision\": 0-12, \"tts\": 0-12}, "
                            "\"reason\": \"...\", \"confidence\": 0-1}]}. "
                            "Use only the aliases auxiliary, coding, agentic, vision, tts. Favor explicit capability and modality fit over name heuristics. "
                            "Only assign tts when the model can produce speech-style audio output; do not classify music generators such as Lyria into tts. Vision and tts do not require tool calling; auxiliary, coding, and agentic do."
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
            shortlist = [
                model
                for model in sorted(models, key=lambda model: self._score_breakdown(alias, model)["total_score"], reverse=True)
                if self._model_is_routable(model, alias=alias)
            ][: self.config.ranking_shortlist_size]
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

    def _family_bias(self, alias: str, model: ProviderModel) -> tuple[str | None, float]:
        primary_matches, description_matches = self._family_matches(alias, model)
        family_bonus_map = self._family_bonus_map(alias)
        if primary_matches:
            family_name = next((family for family in family_bonus_map if family in primary_matches), primary_matches[0])
            return family_name, family_bonus_map.get(family_name, 0.0)
        if description_matches:
            family_name = next((family for family in family_bonus_map if family in description_matches), description_matches[0])
            return family_name, round(family_bonus_map.get(family_name, 0.0) * 0.2, 3)
        return None, 0.0

    def _family_matches(self, alias: str, model: ProviderModel) -> tuple[list[str], list[str]]:
        priors = _FAMILY_PRIORS_BY_ALIAS.get(alias)
        if not priors:
            return [], []
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        primary_haystack = " ".join(
            str(value).lower()
            for value in (
                model.id,
                metadata.get("name"),
            )
            if value
        )
        description_haystack = str(metadata.get("description", "")).lower()
        primary_matches: list[str] = []
        description_matches: list[str] = []
        for family_name, tokens in priors:
            if any(token in primary_haystack for token in tokens):
                primary_matches.append(family_name)
                continue
            if description_haystack and any(token in description_haystack for token in tokens):
                description_matches.append(family_name)
        return primary_matches, description_matches

    def _family_bonus_map(self, alias: str) -> dict[str, float]:
        priors = _FAMILY_PRIORS_BY_ALIAS.get(alias)
        if not priors:
            return {}
        present_families: list[str] = []
        for family_name, _tokens in priors:
            for candidate in self._inventory_for_all():
                if not self._model_is_routable(candidate, alias=alias):
                    continue
                if not self._model_effectively_enabled(candidate.provider, candidate.id):
                    continue
                primary_matches, _ = self._family_matches(alias, candidate)
                if family_name in primary_matches:
                    present_families.append(family_name)
                    break
        step = _FAMILY_RANK_STEP_BY_ALIAS.get(alias, 1.0)
        family_count = len(present_families)
        return {
            family_name: round((family_count - index) * step, 3)
            for index, family_name in enumerate(present_families)
        }

    def _parameter_bias(self, alias: str, model: ProviderModel, *, family_name: str | None) -> tuple[float | None, float]:
        parameter_count = self._parameter_count_b(model)
        size_hint = self._size_hint(model)
        if alias == "auxiliary":
            if parameter_count is None:
                return None, -min(max(size_hint, 0.0) * 2.0, 4.0)
            return parameter_count, -min(parameter_count * 0.18, 8.0)
        if alias == "tts":
            return parameter_count, 0.0
        if family_name is None:
            return parameter_count, 0.0
        largest_signature = self._largest_family_size_signature(alias, family_name)
        current_signature = self._size_signature(model)
        if largest_signature is None or current_signature >= largest_signature:
            return parameter_count, 0.0
        parameter_gap = max(largest_signature[1] - current_signature[1], 0.0)
        size_hint_gap = max(largest_signature[2] - current_signature[2], 0.0)
        if alias == "vision":
            penalty = min((parameter_gap * 0.32) + (size_hint_gap * 2.0), 12.0)
        elif alias == "coding":
            penalty = min((parameter_gap * 0.08) + (size_hint_gap * 4.0), 10.0)
        elif alias == "agentic":
            penalty = min((parameter_gap * 0.06) + (size_hint_gap * 5.0), 16.0)
        else:
            penalty = 0.0
        return parameter_count, -round(penalty, 3)

    def _largest_family_size_signature(self, alias: str, family_name: str) -> tuple[int, float, float] | None:
        best: tuple[int, float, float] | None = None
        for sibling in self._inventory_for_all():
            if not self._model_is_routable(sibling, alias=alias):
                continue
            primary_matches, _ = self._family_matches(alias, sibling)
            matched_families = set(primary_matches)
            if family_name not in matched_families:
                continue
            signature = self._size_signature(sibling)
            if best is None or signature > best:
                best = signature
        return best

    def _size_signature(self, model: ProviderModel) -> tuple[int, float, float]:
        parameter_count = self._parameter_count_b(model)
        return (1 if parameter_count is not None else 0, parameter_count or 0.0, self._size_hint(model))

    def _size_hint(self, model: ProviderModel) -> float:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        haystack = " ".join(
            str(value).lower()
            for value in (
                model.id,
                metadata.get("name"),
            )
            if value
        )
        return round(sum(weight for token, weight in _SIZE_HINTS if token in haystack), 3)

    def _parameter_count_b(self, model: ProviderModel) -> float | None:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        haystack = " ".join(
            str(value).lower()
            for value in (
                model.id,
                metadata.get("name"),
            )
            if value
        )
        matches = [float(match) for match in re.findall(r"(?<!\d)(\d+(?:\.\d+)?)b(?![a-z])", haystack)]
        if not matches:
            return None
        return max(matches)

    def _recency_bias(self, model: ProviderModel) -> float:
        metadata = model.metadata if isinstance(model.metadata, dict) else {}
        created = metadata.get("created")
        try:
            created_value = float(created)
        except (TypeError, ValueError):
            return 0.0
        now = time.time()
        if created_value <= 0 or created_value > now:
            return 0.0
        age_days = (now - created_value) / 86400.0
        if age_days <= 30:
            return 18.0
        if age_days <= 90:
            return 12.0
        if age_days <= 180:
            return 8.0
        if age_days <= 365:
            return 4.0
        return 0.0

    def _model_override_payload(self, provider_name: str, backend_model: str) -> dict[str, Any]:
        overrides = self._effective_overrides()
        return {
            "provider": overrides["provider_map"].get(provider_name),
            "model": overrides["model_map"].get(self._model_key(provider_name, backend_model)),
        }

    @staticmethod
    def _model_key(provider_name: str, backend_model: str) -> str:
        return f"{provider_name}::{backend_model}"

    def _primary_alias_for_model(self, model: ProviderModel) -> str | None:
        lowered = model.id.lower()
        best_alias: str | None = None
        best_key: tuple[float, float, float, float] | None = None
        for alias in _ALIASES:
            if not self._model_is_routable(model, alias=alias):
                continue
            breakdown = self._score_breakdown(alias, model)
            alias_score = breakdown["total_score"]
            if alias_score <= 0:
                continue
            key = (
                alias_score,
                breakdown["learned_ranking_score"],
                breakdown.get("family_bias", 0.0),
                1.0 if alias in model.tags else 0.0,
                1.0 if any(token in lowered for token in _ALIAS_HINTS.get(alias, ())) else 0.0,
            )
            if best_key is None or key > best_key:
                best_alias = alias
                best_key = key
        return best_alias

    def _alias_for_model_id(self, model_id: str) -> str | None:
        for alias, tokens in _ALIAS_HINTS.items():
            if any(token in model_id.lower() for token in tokens):
                return alias
        return None

    def _log_event(self, event: str, **fields: Any) -> None:
        logger.info("router_event %s", json.dumps({"event": event, **fields}, sort_keys=True))
