from __future__ import annotations

import json
import time
from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, TimeoutError, TransportError

from .base import (
    NormalizedProviderError,
    ProviderChatResult,
    ProviderChatStreamEvent,
    ProviderChatStreamResult,
    ProviderChatStreamState,
    ProviderModel,
)


def _is_zeroish(value: Any) -> bool:
    if value in (0, 0.0, "0", "0.0", "0.00", "0.000000"):
        return True
    if value is None:
        return False
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


class OpenRouterProvider:
    name = "openrouter"

    def __init__(self, api_key: str, *, base_url: str, http_referer: str | None = None, title: str | None = None, transport: httpx.BaseTransport | None = None, default_timeout: float = 30.0):
        headers = {"Authorization": f"Bearer {api_key}"}
        if http_referer:
            headers["HTTP-Referer"] = http_referer
        if title:
            headers["X-Title"] = title
        self.client = BaseHttpClient(base_url.rstrip("/"), default_headers=headers, default_timeout=default_timeout, transport=transport)

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        payload = self.client.request_json("GET", "/models", timeout=timeout)
        models: list[ProviderModel] = []
        for raw in payload.get("data", []):
            model_id = str(raw.get("id", "")).strip()
            if not model_id:
                continue
            pricing = raw.get("pricing") or {}
            is_free = model_id.endswith(":free") or (_is_zeroish(pricing.get("prompt")) and _is_zeroish(pricing.get("completion")))
            models.append(
                ProviderModel(
                    id=model_id,
                    provider=self.name,
                    is_free=is_free,
                    tags=self._tags_for_model(model_id),
                    metadata={"name": raw.get("name"), "context_length": raw.get("context_length")},
                )
            )
        return models

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        body = dict(payload)
        body["model"] = backend_model
        try:
            response = self.client.request_json("POST", "/chat/completions", json_body=body, timeout=timeout)
        except TimeoutError as exc:
            raise NormalizedProviderError("timeout", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
        except TransportError as exc:
            raise NormalizedProviderError("transport_error", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
        except HttpStatusError as exc:
            raise self._normalize_http_error(exc, backend_model=backend_model) from exc
        return ProviderChatResult(payload=response, provider=self.name, backend_model=str(response.get("model") or backend_model))

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        body = dict(payload)
        body["model"] = backend_model
        body["stream"] = True
        request_timeout = timeout or self.client.default_timeout
        state = ProviderChatStreamState()
        started_at = time.monotonic()
        tool_calls_acc: dict[int, dict[str, Any]] = {}
        finish_reason: str | None = None

        def stream_chunks():
            spec = self.client.build_request_spec("POST", "/chat/completions", json_body=body, timeout=request_timeout)
            url = f"{self.client.base_url}{spec.path}"
            try:
                with self.client._client(spec.timeout) as client:
                    with client.stream(spec.method, url, params=spec.params, json=spec.json_body, headers=spec.headers) as response:
                        if response.is_error:
                            details: Any = None
                            try:
                                details = response.json()
                            except Exception:
                                details = response.text or None
                            raise self._normalize_http_error(
                                HttpStatusError(
                                    f"remote service returned HTTP {response.status_code}",
                                    status_code=response.status_code,
                                    details=details,
                                ),
                                backend_model=backend_model,
                            )
                        for line in response.iter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                payload_chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue
                            if isinstance(payload_chunk.get("usage"), dict):
                                state.usage = payload_chunk["usage"]
                            choices = payload_chunk.get("choices") or []
                            if not choices:
                                yield ProviderChatStreamEvent(
                                    usage=state.usage,
                                    raw_chunk=payload_chunk,
                                )
                                continue
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
                                            "function": {
                                                "name": "",
                                                "arguments": "",
                                            },
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
                            if isinstance(choice_finish_reason, str) and choice_finish_reason:
                                finish_reason = choice_finish_reason
                            yield ProviderChatStreamEvent(
                                content=content,
                                reasoning=reasoning,
                                tool_calls=tool_calls,
                                finish_reason=choice_finish_reason if isinstance(choice_finish_reason, str) else None,
                                usage=state.usage,
                                raw_chunk=payload_chunk,
                            )
            except TimeoutError as exc:
                raise NormalizedProviderError("timeout", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
            except TransportError as exc:
                raise NormalizedProviderError("transport_error", str(exc), provider=self.name, backend_model=backend_model, retryable=True, details=exc.details) from exc
            except HttpStatusError as exc:
                raise self._normalize_http_error(exc, backend_model=backend_model) from exc
            if state.final_payload is None:
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
                state.final_payload = {
                    "id": f"chatcmpl-{backend_model}",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": message,
                            "finish_reason": finish_reason or ("tool_calls" if tool_calls_acc else "stop"),
                        }
                    ],
                    "usage": state.usage,
                }

        return ProviderChatStreamResult(chunks=stream_chunks(), provider=self.name, backend_model=backend_model, state=state)

    @staticmethod
    def _tags_for_model(model_id: str) -> tuple[str, ...]:
        lowered = model_id.lower()
        tags: list[str] = []
        if any(token in lowered for token in ("code", "coder", "devstral", "qwen", "deepseek")):
            tags.append("coding")
        if any(token in lowered for token in ("mini", "small", "flash-lite", "nano")):
            tags.append("lightweight")
        if any(token in lowered for token in ("large", "70b", "72b", "r1", "reason", "sonnet", "opus")):
            tags.append("heavyweight")
        return tuple(tags)

    def _normalize_http_error(self, exc: HttpStatusError, *, backend_model: str) -> NormalizedProviderError:
        status = exc.status_code
        if status in {401, 403}:
            return NormalizedProviderError("unauthorized", exc.message, provider=self.name, backend_model=backend_model, retryable=False, details=exc.details)
        if status == 404:
            return NormalizedProviderError("model_missing", exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if status == 429:
            return NormalizedProviderError("rate_limited", exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if status >= 500:
            return NormalizedProviderError("server_error", exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        return NormalizedProviderError("bad_request", exc.message, provider=self.name, backend_model=backend_model, retryable=False, details=exc.details)
