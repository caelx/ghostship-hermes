from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
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


def _normalized_error_details(exc: HttpStatusError) -> dict[str, Any]:
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
        payload["temporary_throttle"] = True
        payload["provider_pacing"] = True
    lowered = message.lower()
    if "quota" in lowered or "insufficient balance" in lowered or "credits" in lowered:
        payload["hard_exhaustion"] = True
    return payload


class _InlineScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self._in_script = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "script":
            self._in_script = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_script:
            self.scripts.append("".join(self._buffer))
            self._in_script = False
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._buffer.append(data)


class NvidiaBuildProvider:
    name = "nvidia-build"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str,
        catalog_url: str = "https://build.nvidia.com/models",
        transport: httpx.BaseTransport | None = None,
        default_timeout: float = 30.0,
    ):
        self.client = BaseHttpClient(
            base_url.rstrip("/"),
            default_headers={"Authorization": f"Bearer {api_key}"},
            default_timeout=default_timeout,
            transport=transport,
        )
        self.catalog_url = catalog_url
        self._transport = transport
        self._default_timeout = default_timeout

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        html = self._fetch_catalog_html(timeout=timeout)
        resources = self._parse_catalog_resources(html)
        models: list[ProviderModel] = []
        for resource in resources:
            model = self._resource_to_model(resource)
            if model is not None:
                models.append(model)
        models.sort(key=lambda item: item.id)
        return models

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        body = dict(payload)
        body.pop("stream", None)
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
            nonlocal finish_reason
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
                                    headers=dict(response.headers),
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
                                yield ProviderChatStreamEvent(usage=state.usage, raw_chunk=payload_chunk)
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

    def _fetch_catalog_html(self, *, timeout: float | None) -> str:
        request_timeout = timeout or self._default_timeout
        with httpx.Client(transport=self._transport, timeout=request_timeout, follow_redirects=True) as client:
            response = client.get(self.catalog_url, headers={"Accept": "text/html,application/xhtml+xml"})
            response.raise_for_status()
            return response.text

    @classmethod
    def _parse_catalog_resources(cls, html: str) -> list[dict[str, Any]]:
        parser = _InlineScriptParser()
        parser.feed(html)
        blob_parts: list[str] = []
        for script in parser.scripts:
            match = re.search(r'self\.__next_f\.push\(\[1,"(.*)"\]\)\s*$', script, re.S)
            if not match:
                continue
            blob_parts.append(json.loads(f'"{match.group(1)}"'))
        blob = "".join(blob_parts)
        resources: list[dict[str, Any]] = []
        for raw in re.findall(r'\{"orgName":.*?"guestAccess":(?:true|false)\}', blob, re.S):
            try:
                resources.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        return resources

    @classmethod
    def _resource_to_model(cls, resource: dict[str, Any]) -> ProviderModel | None:
        resource_id = str(resource.get("resourceId") or "").strip()
        if "/" not in resource_id:
            return None
        _, backend_name = resource_id.split("/", 1)
        publisher = next(iter(cls._label_values(resource, "publisher")), "").strip()
        backend_model = f"{publisher}/{backend_name}" if publisher else backend_name
        metadata = cls._metadata_for_resource(resource, backend_model=backend_model)
        if not cls._is_current_free_endpoint(resource):
            return None
        return ProviderModel(
            id=backend_model,
            provider=cls.name,
            is_free=True,
            tags=cls._tags_for_resource(resource, backend_model=backend_model),
            metadata=metadata,
        )

    @staticmethod
    def _label_values(resource: dict[str, Any], key: str) -> tuple[str, ...]:
        values: list[str] = []
        for label in resource.get("labels") or []:
            if not isinstance(label, dict) or label.get("key") != key:
                continue
            for value in label.get("values") or []:
                text = str(value).strip()
                if text:
                    values.append(text)
        return tuple(values)

    @classmethod
    def _is_current_free_endpoint(cls, resource: dict[str, Any]) -> bool:
        nim_types = cls._label_values(resource, "nimType")
        if any("Deprecated" in value for value in nim_types):
            return False
        return any(value == "Free Endpoint" for value in nim_types)

    @classmethod
    def _tags_for_resource(cls, resource: dict[str, Any], *, backend_model: str) -> tuple[str, ...]:
        lowered = f"{backend_model} {resource.get('displayName', '')} {resource.get('description', '')}".lower()
        label_values = " ".join(
            value.lower()
            for label in resource.get("labels") or []
            if isinstance(label, dict)
            for value in label.get("values") or []
        )
        haystack = f"{lowered} {label_values}"
        tags: list[str] = []
        if any(token in haystack for token in ("agentic", "tool use", "tool calling", "reasoning", "coding", "coder", "code", "thinking")):
            tags.append("agentic")
        if any(token in haystack for token in ("vision", "multimodal", "image", "video")):
            tags.append("vision")
        if any(token in haystack for token in ("audio", "speech", "voice", "asr", "tts")):
            tags.append("tts")
        return tuple(dict.fromkeys(tags))

    @classmethod
    def _metadata_for_resource(cls, resource: dict[str, Any], *, backend_model: str) -> dict[str, Any]:
        input_modalities = ["text"]
        output_modalities = ["text"]
        general_values = " ".join(cls._label_values(resource, "general")).lower()
        if any(token in general_values for token in ("multimodal", "vision", "video")):
            input_modalities = ["text", "image"]
        if any(token in general_values for token in ("speech", "audio", "voice")):
            output_modalities = ["audio"]
        attributes = {
            str(item.get("key")): item.get("value")
            for item in resource.get("attributes") or []
            if isinstance(item, dict) and item.get("key")
        }
        return {
            "name": str(resource.get("displayName") or backend_model),
            "description": str(resource.get("description") or "NVIDIA Build free endpoint."),
            "created": cls._created_timestamp(resource.get("dateCreated")),
            "input_modalities": input_modalities,
            "output_modalities": output_modalities,
            "catalog_source": "build.nvidia.com/models",
            "catalog_resource_id": resource.get("resourceId"),
            "catalog_org_name": resource.get("orgName"),
            "catalog_labels": resource.get("labels") or [],
            "logo": attributes.get("logo"),
            "preview": str(attributes.get("PREVIEW") or "").lower() == "true",
            "available": str(attributes.get("AVAILABLE") or "").lower() == "true",
        }

    @staticmethod
    def _created_timestamp(value: Any) -> float | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
        except Exception:
            return None

    def _normalize_http_error(self, exc: HttpStatusError, *, backend_model: str) -> NormalizedProviderError:
        status = exc.status_code
        details = _normalized_error_details(exc)
        message = _extract_error_message(details) or exc.message
        if status in {401, 403}:
            return NormalizedProviderError("unauthorized", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
        if status == 404:
            return NormalizedProviderError("model_missing", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        if status == 429:
            category = "quota_exhausted" if details.get("hard_exhaustion") else "rate_limited"
            return NormalizedProviderError(category, message, provider=self.name, backend_model=backend_model, retryable=(category == "rate_limited"), details=details)
        if status >= 500:
            return NormalizedProviderError("server_error", message, provider=self.name, backend_model=backend_model, retryable=True, details=details)
        return NormalizedProviderError("bad_request", message, provider=self.name, backend_model=backend_model, retryable=False, details=details)
