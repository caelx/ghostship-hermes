from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

import httpx

from .base import (
    NormalizedProviderError,
    ProviderChatResult,
    ProviderChatStreamEvent,
    ProviderChatStreamResult,
    ProviderChatStreamState,
    ProviderModel,
)
from ..http_client import BaseHttpClient, HttpStatusError, TimeoutError, TransportError

_SUPPORTED_FAMILIES = (
    "chat_completions",
    "responses",
    "messages",
    "google_generate_content",
)


def _normalize_model_key(model_id: str) -> str:
    lowered = model_id.strip().lower()
    tail = lowered.split("/", 1)[1] if "/" in lowered else lowered
    if tail.endswith(":free"):
        tail = tail[:-5]
    if tail.endswith("-free"):
        tail = tail[:-5]
    return "".join(char for char in tail if char.isalnum())


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
                continue
            if item.get("type") in {"input_text", "output_text", "text"}:
                candidate = item.get("text")
                if isinstance(candidate, str):
                    parts.append(candidate)
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return str(content) if content is not None else ""


def _extract_error_message(details: Any) -> str:
    if isinstance(details, str):
        return details
    if isinstance(details, dict):
        error = details.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
        message = details.get("message")
        if isinstance(message, str):
            return message
    return ""

def _retry_after_seconds(headers: dict[str, str] | None) -> float | None:
    if not headers:
        return None
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    return value if value > 0 else None


def _normalized_http_details(exc: HttpStatusError) -> dict[str, Any]:
    payload: dict[str, Any]
    if isinstance(exc.details, dict):
        payload = dict(exc.details)
    elif exc.details is None:
        payload = {}
    else:
        payload = {"message": str(exc.details)}
    message = _extract_error_message(payload) or exc.message
    if message:
        payload.setdefault("message", message)
    retry_after = _retry_after_seconds(exc.headers)
    if retry_after is not None:
        payload["retry_after_seconds"] = retry_after
    lowered = message.lower()
    if "freeusagelimiterror" in lowered or "rate limit exceeded" in lowered or "throttling" in lowered or retry_after is not None:
        payload["temporary_throttle"] = True
        payload["provider_pacing"] = True
    if "quota" in lowered or ("monthly" in lowered and "limit" in lowered):
        payload["hard_exhaustion"] = True
    return payload



class OpencodeZenProvider:
    name = "opencode-zen"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
        default_timeout: float = 30.0,
        provider_name: str = "opencode-zen",
        force_free_models: bool = False,
    ):
        self.name = provider_name
        self._force_free_models = force_free_models
        self.client = BaseHttpClient(
            base_url.rstrip("/"),
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "x-api-key": api_key,
                "User-Agent": "ghostship-hermes-router",
            },
            default_timeout=default_timeout,
            transport=transport,
        )
        self._metadata_cache: dict[str, dict[str, Any]] = {}
        self._family_cache: dict[str, str] = {}
        self._model_cache: dict[str, ProviderModel] = {}

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        payload = self.client.request_json("GET", "/models", timeout=timeout)
        public_metadata = self._fetch_public_metadata(timeout=timeout)
        openrouter_metadata = self._fetch_openrouter_metadata(timeout=timeout)
        models: list[ProviderModel] = []
        for raw in payload.get("data", []):
            model_id = str(raw.get("id", "")).strip()
            if not model_id:
                continue
            metadata = public_metadata.get(model_id, {})
            openrouter_match = self._match_openrouter_metadata(model_id, metadata, openrouter_metadata)
            flattened_metadata = self._flatten_model_metadata(model_id, metadata, openrouter_match)
            endpoint_family = self._infer_endpoint_family(model_id, flattened_metadata)
            flattened_metadata["endpoint_family"] = endpoint_family
            model = ProviderModel(
                id=model_id,
                provider=self.name,
                is_free=self._force_free_models or self._is_free_model(model_id, flattened_metadata),
                tags=self._tags_for_model(model_id),
                metadata=flattened_metadata,
            )
            models.append(model)
            self._metadata_cache[model_id] = flattened_metadata
            self._family_cache.setdefault(model_id, endpoint_family)
            self._model_cache[model_id] = model
        return models

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        family_order = self._endpoint_family_order(backend_model)
        last_error: NormalizedProviderError | None = None
        for family in family_order:
            try:
                result = self._chat_with_family(family, backend_model, payload, timeout=timeout)
                self._family_cache[backend_model] = family
                return result
            except NormalizedProviderError as exc:
                last_error = exc
                if self._should_try_next_family(exc):
                    continue
                raise
        if last_error is not None:
            raise last_error
        raise NormalizedProviderError(
            "bad_request",
            f"No supported OpenCode Zen endpoint family worked for model '{backend_model}'.",
            provider=self.name,
            backend_model=backend_model,
            retryable=False,
        )

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        family_order = self._endpoint_family_order(backend_model)
        last_error: NormalizedProviderError | None = None
        for family in family_order:
            try:
                result = self._stream_with_family(family, backend_model, payload, timeout=timeout)
                self._family_cache[backend_model] = family
                return result
            except NormalizedProviderError as exc:
                last_error = exc
                if self._should_try_next_family(exc):
                    continue
                raise
        if last_error is not None:
            raise last_error
        raise NormalizedProviderError(
            "bad_request",
            f"No supported OpenCode Zen endpoint family worked for model '{backend_model}'.",
            provider=self.name,
            backend_model=backend_model,
            retryable=False,
        )

    def _endpoint_family_order(self, model_id: str) -> list[str]:
        inferred = self._family_cache.get(model_id) or self._infer_endpoint_family(model_id, self._metadata_cache.get(model_id, {}))
        ordered: list[str] = []
        for family in (inferred, *_SUPPORTED_FAMILIES):
            if family and family not in ordered:
                ordered.append(family)
        return ordered

    def _should_try_next_family(self, exc: NormalizedProviderError) -> bool:
        message = _extract_error_message(exc.details).lower()
        if exc.category == "endpoint_family_mismatch":
            return True
        if "not supported for format" in message:
            return True
        if "missing api key" in message:
            return True
        if "input_tokens" in message:
            return True
        return False

    def _chat_with_family(self, family: str, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        body, path = self._build_request(family, backend_model, payload)
        started_at = time.monotonic()
        try:
            response = self.client.request_json("POST", path, json_body=body, timeout=timeout)
        except TimeoutError as exc:
            raise NormalizedProviderError("timeout", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
        except TransportError as exc:
            raise NormalizedProviderError("transport_error", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
        except HttpStatusError as exc:
            raise self._normalize_http_error(exc, backend_model=backend_model) from exc
        latency_ms = round((time.monotonic() - started_at) * 1000, 2)
        normalized = self._normalize_response(family, backend_model, response)
        return ProviderChatResult(
            payload=normalized,
            provider=self.name,
            backend_model=backend_model,
            first_text_latency_ms=latency_ms,
        )

    def _stream_with_family(self, family: str, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        body, path, params = self._build_stream_request(family, backend_model, payload)
        request_timeout = timeout or self.client.default_timeout
        state = ProviderChatStreamState()
        started_at = time.monotonic()
        tool_calls_acc: dict[int, dict[str, Any]] = {}
        finish_reason: str | None = None

        def stream_chunks():
            nonlocal finish_reason
            spec = self.client.build_request_spec("POST", path, json_body=body, params=params, timeout=request_timeout)
            url = f"{self.client.base_url}{spec.path}"
            try:
                with self.client._client(spec.timeout) as client:
                    with client.stream(spec.method, url, params=spec.params, json=spec.json_body, headers=spec.headers) as response:
                        if response.is_error:
                            details: Any = None
                            response.read()
                            try:
                                details = response.json()
                            except Exception:
                                details = response.text or None
                            raise self._normalize_http_error(
                                HttpStatusError(
                                    f"remote service returned HTTP {response.status_code}",
                                    status_code=response.status_code,
                                    details=details,
                                    headers=dict(response.headers),
                                ),
                                backend_model=backend_model,
                            )
                        for event_name, event_data in self._iter_sse_events(response.iter_lines()):
                            if event_data == "[DONE]":
                                break
                            for event in self._stream_events_from_sse(
                                family,
                                backend_model,
                                event_name,
                                event_data,
                                state=state,
                                tool_calls_acc=tool_calls_acc,
                                started_at=started_at,
                            ):
                                if isinstance(event.finish_reason, str) and event.finish_reason:
                                    finish_reason = event.finish_reason
                                yield event
            except TimeoutError as exc:
                raise NormalizedProviderError("timeout", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
            except TransportError as exc:
                raise NormalizedProviderError("transport_error", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
            except HttpStatusError as exc:
                raise self._normalize_http_error(exc, backend_model=backend_model) from exc
            if state.final_payload is None:
                state.final_payload = self._final_stream_payload(
                    family,
                    backend_model,
                    state=state,
                    finish_reason=finish_reason,
                    tool_calls_acc=tool_calls_acc,
                )

        return ProviderChatStreamResult(
            chunks=stream_chunks(),
            provider=self.name,
            backend_model=backend_model,
            state=state,
        )

    def _build_request(self, family: str, backend_model: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        messages = payload.get("messages", [])
        if family == "chat_completions":
            body = dict(payload)
            body.pop("stream", None)
            body.pop("stream_options", None)
            body["messages"] = self._normalize_chat_messages_for_model(backend_model, body.get("messages", []))
            body["model"] = backend_model
            return body, "/chat/completions"
        if family == "responses":
            body: dict[str, Any] = {
                "model": backend_model,
                "input": self._build_responses_input(messages),
            }
            if payload.get("temperature") is not None:
                body["temperature"] = payload["temperature"]
            if payload.get("max_tokens") is not None:
                body["max_output_tokens"] = payload["max_tokens"]
            return body, "/responses"
        if family == "messages":
            system_prompt = "\n".join(_text_from_content(message.get("content")) for message in messages if message.get("role") == "system").strip()
            body = {
                "model": backend_model,
                "messages": self._build_messages_input(messages),
                "max_tokens": payload.get("max_tokens") or 1024,
            }
            if system_prompt:
                body["system"] = system_prompt
            if payload.get("temperature") is not None:
                body["temperature"] = payload["temperature"]
            return body, "/messages"
        if family == "google_generate_content":
            body = {
                "contents": self._build_google_contents(messages),
            }
            system_prompt = "\n".join(_text_from_content(message.get("content")) for message in messages if message.get("role") == "system").strip()
            if system_prompt:
                body["system_instruction"] = {"parts": [{"text": system_prompt}]}
            if payload.get("temperature") is not None or payload.get("max_tokens") is not None:
                body["generationConfig"] = {
                    key: value
                    for key, value in {
                        "temperature": payload.get("temperature"),
                        "maxOutputTokens": payload.get("max_tokens"),
                    }.items()
                    if value is not None
                }
            return body, f"/models/{backend_model}:generateContent"
        raise NormalizedProviderError("bad_request", f"Unsupported endpoint family '{family}'.", provider=self.name, backend_model=backend_model)

    @staticmethod
    def _normalize_chat_messages_for_model(backend_model: str, messages: Any) -> list[dict[str, Any]]:
        normalized = [dict(message) for message in messages if isinstance(message, dict)]
        if not backend_model.startswith("deepseek-"):
            return normalized
        for message in normalized:
            if message.get("role") == "assistant" and isinstance(message.get("tool_calls"), list) and "reasoning_content" not in message:
                message["reasoning_content"] = ""
        return normalized

    def _build_stream_request(self, family: str, backend_model: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any] | None]:
        body, path = self._build_request(family, backend_model, payload)
        params: dict[str, Any] | None = None
        if family == "google_generate_content":
            stream_path = f"/models/{backend_model}:streamGenerateContent"
            return body, stream_path, {"alt": "sse"}
        body["stream"] = True
        return body, path, params

    @staticmethod
    def _build_responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "role": message.get("role", "user"),
                "content": [{"type": "input_text", "text": _text_from_content(message.get("content"))}],
            }
            for message in messages
            if message.get("role") in {"system", "user", "assistant"}
        ]

    @staticmethod
    def _build_messages_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        built: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                continue
            built.append(
                {
                    "role": "assistant" if role == "assistant" else "user",
                    "content": _text_from_content(message.get("content")),
                }
            )
        return built or [{"role": "user", "content": ""}]

    @staticmethod
    def _build_google_contents(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                continue
            contents.append(
                {
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": _text_from_content(message.get("content"))}],
                }
            )
        return contents or [{"role": "user", "parts": [{"text": ""}]}]

    def _normalize_response(self, family: str, backend_model: str, payload: dict[str, Any]) -> dict[str, Any]:
        if family == "chat_completions":
            return payload
        if family == "responses":
            text = self._extract_responses_text(payload)
            return {
                "id": payload.get("id", f"chatcmpl-{backend_model}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": payload.get("usage"),
            }
        if family == "messages":
            text = self._extract_anthropic_text(payload)
            return {
                "id": payload.get("id", f"chatcmpl-{backend_model}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": payload.get("stop_reason", "stop")}],
                "usage": payload.get("usage"),
            }
        if family == "google_generate_content":
            text = self._extract_google_text(payload)
            return {
                "id": f"chatcmpl-{backend_model}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": payload.get("usageMetadata"),
            }
        return payload

    def _final_stream_payload(
        self,
        family: str,
        backend_model: str,
        *,
        state: ProviderChatStreamState,
        finish_reason: str | None,
        tool_calls_acc: dict[int, dict[str, Any]],
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "assistant"}
        if state.emitted_text:
            message["content"] = state.emitted_text
        if state.emitted_reasoning:
            message["reasoning_content"] = state.emitted_reasoning
        if tool_calls_acc:
            message["tool_calls"] = [
                {
                    "id": item.get("id"),
                    "type": item.get("type") or "function",
                    "function": {
                        "name": item.get("function", {}).get("name", ""),
                        "arguments": item.get("function", {}).get("arguments", ""),
                    },
                }
                for _, item in sorted(tool_calls_acc.items())
            ]
        resolved_finish = finish_reason or ("tool_calls" if tool_calls_acc else "stop")
        payload = {
            "id": f"chatcmpl-{backend_model}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": backend_model,
            "choices": [{"index": 0, "message": message, "finish_reason": resolved_finish}],
            "usage": state.usage,
        }
        if family == "google_generate_content":
            payload["usage"] = state.usage
        return payload

    def _stream_events_from_sse(
        self,
        family: str,
        backend_model: str,
        event_name: str | None,
        event_data: str,
        *,
        state: ProviderChatStreamState,
        tool_calls_acc: dict[int, dict[str, Any]],
        started_at: float,
    ) -> list[ProviderChatStreamEvent]:
        try:
            payload = json.loads(event_data)
        except json.JSONDecodeError:
            return []
        if family == "chat_completions":
            return self._chat_completion_stream_events(
                backend_model,
                payload,
                state=state,
                tool_calls_acc=tool_calls_acc,
                started_at=started_at,
            )
        if family == "responses":
            return self._responses_stream_events(
                payload,
                backend_model=backend_model,
                event_name=event_name,
                state=state,
                started_at=started_at,
            )
        if family == "messages":
            return self._messages_stream_events(payload, event_name=event_name, state=state, started_at=started_at)
        if family == "google_generate_content":
            return self._google_stream_events(payload, state=state, started_at=started_at)
        return []

    @staticmethod
    def _iter_sse_events(lines: Any):
        event_name: str | None = None
        data_lines: list[str] = []
        for raw_line in lines:
            line = raw_line.decode() if isinstance(raw_line, bytes) else str(raw_line)
            if line == "":
                if data_lines:
                    yield event_name, "\n".join(data_lines)
                event_name = None
                data_lines = []
                continue
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_name = line[6:].strip() or None
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if data_lines:
            yield event_name, "\n".join(data_lines)

    def _chat_completion_stream_events(
        self,
        backend_model: str,
        payload_chunk: dict[str, Any],
        *,
        state: ProviderChatStreamState,
        tool_calls_acc: dict[int, dict[str, Any]],
        started_at: float,
    ) -> list[ProviderChatStreamEvent]:
        events: list[ProviderChatStreamEvent] = []
        if isinstance(payload_chunk.get("usage"), dict):
            state.usage = payload_chunk["usage"]
        choices = payload_chunk.get("choices") or []
        if not choices:
            if state.usage:
                return [ProviderChatStreamEvent(usage=state.usage, raw_chunk=payload_chunk)]
            return []
        choice = choices[0] or {}
        delta = choice.get("delta") or {}
        content = delta.get("content")
        if isinstance(content, str) and content:
            if state.first_text_latency_ms is None:
                state.first_text_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            state.emitted_text += content
        else:
            content = None
        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            state.emitted_reasoning += reasoning
        else:
            reasoning = None
        raw_tool_calls = delta.get("tool_calls")
        tool_calls: list[dict[str, Any]] | None = None
        if isinstance(raw_tool_calls, list):
            tool_calls = []
            for raw_tool_call in raw_tool_calls:
                if not isinstance(raw_tool_call, dict):
                    continue
                index = int(raw_tool_call.get("index") or 0)
                function = raw_tool_call.get("function") if isinstance(raw_tool_call.get("function"), dict) else {}
                entry = tool_calls_acc.setdefault(
                    index,
                    {
                        "index": index,
                        "id": raw_tool_call.get("id"),
                        "type": raw_tool_call.get("type") or "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                if raw_tool_call.get("id"):
                    entry["id"] = raw_tool_call["id"]
                if raw_tool_call.get("type"):
                    entry["type"] = raw_tool_call["type"]
                if function.get("name"):
                    entry["function"]["name"] += str(function["name"])
                if function.get("arguments"):
                    entry["function"]["arguments"] += str(function["arguments"])
                tool_calls.append(raw_tool_call)
        choice_finish_reason = choice.get("finish_reason")
        events.append(
            ProviderChatStreamEvent(
                content=content,
                reasoning=reasoning,
                tool_calls=tool_calls,
                finish_reason=choice_finish_reason if isinstance(choice_finish_reason, str) else None,
                usage=state.usage,
                raw_chunk=payload_chunk,
            )
        )
        return events

    def _responses_stream_events(
        self,
        payload: dict[str, Any],
        *,
        backend_model: str,
        event_name: str | None,
        state: ProviderChatStreamState,
        started_at: float,
    ) -> list[ProviderChatStreamEvent]:
        event_type = event_name or str(payload.get("type") or "")
        events: list[ProviderChatStreamEvent] = []
        if event_type == "response.output_text.delta":
            delta = payload.get("delta")
            if isinstance(delta, str) and delta:
                if state.first_text_latency_ms is None:
                    state.first_text_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
                state.emitted_text += delta
                events.append(ProviderChatStreamEvent(content=delta))
        elif event_type == "response.reasoning.delta":
            delta = payload.get("delta")
            if isinstance(delta, str) and delta:
                state.emitted_reasoning += delta
                events.append(ProviderChatStreamEvent(reasoning=delta))
        elif event_type == "response.completed":
            response = payload.get("response") if isinstance(payload.get("response"), dict) else {}
            usage = response.get("usage")
            if isinstance(usage, dict):
                state.usage = usage
            if response:
                state.final_payload = self._normalize_response("responses", backend_model, response)
            events.append(ProviderChatStreamEvent(finish_reason="stop", usage=state.usage))
        return events

    def _messages_stream_events(
        self,
        payload: dict[str, Any],
        *,
        event_name: str | None,
        state: ProviderChatStreamState,
        started_at: float,
    ) -> list[ProviderChatStreamEvent]:
        event_type = event_name or str(payload.get("type") or "")
        events: list[ProviderChatStreamEvent] = []
        if event_type == "message_start":
            message = payload.get("message")
            usage = message.get("usage") if isinstance(message, dict) else None
            if isinstance(usage, dict):
                state.usage = usage
        elif event_type == "content_block_delta":
            delta = payload.get("delta") if isinstance(payload.get("delta"), dict) else {}
            text = delta.get("text") if isinstance(delta.get("text"), str) else None
            reasoning = delta.get("thinking") if isinstance(delta.get("thinking"), str) else None
            if text:
                if state.first_text_latency_ms is None:
                    state.first_text_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
                state.emitted_text += text
            if reasoning:
                state.emitted_reasoning += reasoning
            if text or reasoning:
                events.append(ProviderChatStreamEvent(content=text, reasoning=reasoning))
        elif event_type == "message_delta":
            delta = payload.get("delta") if isinstance(payload.get("delta"), dict) else {}
            usage = payload.get("usage")
            if isinstance(usage, dict):
                state.usage = usage
            finish_reason = delta.get("stop_reason") if isinstance(delta.get("stop_reason"), str) else None
            if finish_reason or state.usage:
                events.append(ProviderChatStreamEvent(finish_reason=finish_reason, usage=state.usage))
        return events

    def _google_stream_events(
        self,
        payload: dict[str, Any],
        *,
        state: ProviderChatStreamState,
        started_at: float,
    ) -> list[ProviderChatStreamEvent]:
        events: list[ProviderChatStreamEvent] = []
        text_parts: list[str] = []
        finish_reason: str | None = None
        for candidate in payload.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            candidate_finish = candidate.get("finishReason")
            if isinstance(candidate_finish, str) and candidate_finish:
                finish_reason = candidate_finish.lower()
            content = candidate.get("content") if isinstance(candidate.get("content"), dict) else {}
            for part in content.get("parts", []):
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
        content_delta = "".join(text_parts)
        if content_delta:
            if state.first_text_latency_ms is None:
                state.first_text_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            state.emitted_text += content_delta
        usage = payload.get("usageMetadata")
        if isinstance(usage, dict):
            state.usage = usage
        if content_delta or finish_reason or state.usage:
            events.append(ProviderChatStreamEvent(content=content_delta or None, finish_reason=finish_reason, usage=state.usage))
        return events

    @staticmethod
    def _extract_chat_completion_text(payload: dict[str, Any]) -> str:
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        return _text_from_content(content)

    @staticmethod
    def _extract_responses_text(payload: dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text:
            return output_text
        parts: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def _extract_anthropic_text(payload: dict[str, Any]) -> str:
        parts: list[str] = []
        for item in payload.get("content", []):
            text = item.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def _extract_google_text(payload: dict[str, Any]) -> str:
        parts: list[str] = []
        for candidate in payload.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
        return "\n".join(parts)

    def _fetch_openrouter_metadata(self, *, timeout: float | None = None) -> dict[str, dict[str, Any]]:
        request_timeout = timeout or self.client.default_timeout
        try:
            with httpx.Client(timeout=request_timeout, follow_redirects=True, headers={"User-Agent": "ghostship-hermes-router"}) as client:
                response = client.get("https://openrouter.ai/api/v1/models")
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return {"by_id": {}, "by_normalized": {}}
        by_id: dict[str, dict[str, Any]] = {}
        by_normalized: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for raw in payload.get("data", []):
            model_id = str(raw.get("id", "")).strip()
            if not model_id:
                continue
            architecture = raw.get("architecture") if isinstance(raw.get("architecture"), dict) else {}
            item = {
                "id": model_id,
                "name": raw.get("name"),
                "description": raw.get("description"),
                "created": raw.get("created"),
                "context_length": raw.get("context_length"),
                "modality": architecture.get("modality"),
                "input_modalities": architecture.get("input_modalities"),
                "output_modalities": architecture.get("output_modalities"),
                "supported_parameters": raw.get("supported_parameters"),
            }
            by_id[model_id] = item
            by_normalized[_normalize_model_key(model_id)].append(item)
        return {"by_id": by_id, "by_normalized": dict(by_normalized)}

    def _match_openrouter_metadata(
        self,
        model_id: str,
        metadata: dict[str, Any],
        openrouter_metadata: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        by_id = openrouter_metadata.get("by_id", {})
        by_normalized = openrouter_metadata.get("by_normalized", {})
        if model_id in by_id:
            return by_id[model_id]
        normalized = _normalize_model_key(model_id)
        matches = list(by_normalized.get(normalized, ()))
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        preferred_free = [item for item in matches if str(item.get("id", "")).endswith(":free")]
        candidates = preferred_free or matches
        candidates.sort(key=lambda item: float(item.get("created") or 0), reverse=True)
        return candidates[0]

    def _flatten_model_metadata(
        self,
        model_id: str,
        provider_metadata: dict[str, Any],
        openrouter_match: dict[str, Any] | None,
    ) -> dict[str, Any]:
        flattened = {
            "name": (openrouter_match or {}).get("name") or model_id,
            "description": (openrouter_match or {}).get("description"),
            "created": (openrouter_match or {}).get("created") or provider_metadata.get("created"),
            "context_length": (openrouter_match or {}).get("context_length"),
            "modality": (openrouter_match or {}).get("modality"),
            "input_modalities": (openrouter_match or {}).get("input_modalities"),
            "output_modalities": (openrouter_match or {}).get("output_modalities"),
            "supported_parameters": (openrouter_match or {}).get("supported_parameters"),
            "provider_metadata": provider_metadata,
        }
        if openrouter_match is not None:
            flattened["openrouter_match_id"] = openrouter_match.get("id")
            flattened["openrouter_metadata"] = openrouter_match
        return flattened

    def _fetch_public_metadata(self, *, timeout: float | None = None) -> dict[str, dict[str, Any]]:
        request_timeout = timeout or self.client.default_timeout
        try:
            with httpx.Client(timeout=request_timeout, follow_redirects=True, headers={"User-Agent": "ghostship-hermes-router"}) as client:
                response = client.get("https://models.dev/api.json")
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return {}
        models = payload.get("opencode", {}).get("models", {})
        return models if isinstance(models, dict) else {}

    @staticmethod
    def _infer_endpoint_family(model_id: str, metadata: dict[str, Any]) -> str:
        lowered = model_id.lower()
        if lowered.startswith("claude-"):
            return "messages"
        if lowered.startswith("gemini-"):
            return "google_generate_content"
        if lowered.startswith("gpt-"):
            return "responses"
        provider_payload = metadata
        if not isinstance(provider_payload.get("provider"), dict) and isinstance(provider_payload.get("provider_metadata"), dict):
            provider_payload = provider_payload.get("provider_metadata") or {}
        provider_npm = ((provider_payload.get("provider") or {}).get("npm") or "").lower()
        if provider_npm.endswith("/anthropic"):
            return "messages"
        if provider_npm.endswith("/google"):
            return "google_generate_content"
        if provider_npm.endswith("/openai"):
            return "responses"
        return "chat_completions"

    @staticmethod
    def _is_free_model(model_id: str, metadata: dict[str, Any]) -> bool:
        lowered = model_id.lower()
        if lowered.endswith("-free") or lowered == "big-pickle":
            return True
        cost = metadata.get("cost") or ((metadata.get("provider_metadata") or {}).get("cost") if isinstance(metadata.get("provider_metadata"), dict) else {}) or {}
        numeric_values = [value for value in cost.values() if isinstance(value, (int, float))]
        return bool(numeric_values) and all(float(value) == 0.0 for value in numeric_values)

    @staticmethod
    def _tags_for_model(model_id: str) -> tuple[str, ...]:
        lowered = model_id.lower()
        tags: list[str] = []
        if any(token in lowered for token in ("code", "coder", "coding", "codex", "deepseek", "devstral", "qwen", "thinking", "reason", "large", "opus", "sonnet", "pro")):
            tags.append("coding")
        if any(token in lowered for token in ("mini", "nano", "flash", "haiku", "free", "small")):
            tags.append("auxiliary")
        if any(token in lowered for token in ("vision", "vl", "image", "video", "multimodal", "omni")):
            tags.append("vision")
        if any(token in lowered for token in ("audio", "speech", "voice", "tts")):
            tags.append("tts")
        return tuple(dict.fromkeys(tags))

    def _normalize_http_error(self, exc: HttpStatusError, *, backend_model: str) -> NormalizedProviderError:
        details = _normalized_http_details(exc)
        message = _extract_error_message(details) or exc.message
        lowered = message.lower()
        if "tool_choice" in lowered and ("not support" in lowered or "no endpoints found" in lowered):
            return NormalizedProviderError("tool_choice_unsupported", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
        if "not supported for format" in lowered:
            return NormalizedProviderError("endpoint_family_mismatch", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        if "missing api key" in lowered:
            return NormalizedProviderError("endpoint_family_mismatch", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        if "insufficient balance" in lowered or "credit required" in lowered:
            details["hard_exhaustion"] = True
            return NormalizedProviderError("insufficient_balance", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
        if exc.status_code in {401, 403}:
            return NormalizedProviderError("unauthorized", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
        if exc.status_code == 404:
            return NormalizedProviderError("model_missing", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        if exc.status_code == 402:
            details["hard_exhaustion"] = True
            return NormalizedProviderError("insufficient_balance", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
        if exc.status_code == 429:
            category = "quota_exhausted" if details.get("hard_exhaustion") else "rate_limited"
            return NormalizedProviderError(category, message, provider=self.name, backend_model=backend_model, retryable=(category == "rate_limited"), details=details)
        if exc.status_code >= 500:
            return NormalizedProviderError("server_error", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        return NormalizedProviderError("bad_request", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
