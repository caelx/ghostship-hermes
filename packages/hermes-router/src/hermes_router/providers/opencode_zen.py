from __future__ import annotations

import json
import time
from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, TimeoutError, TransportError

from .base import NormalizedProviderError, ProviderChatResult, ProviderModel

_SUPPORTED_FAMILIES = (
    "chat_completions",
    "responses",
    "messages",
    "google_generate_content",
)


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


class OpencodeZenProvider:
    name = "opencode-zen"

    def __init__(self, api_key: str, *, base_url: str, transport: httpx.BaseTransport | None = None, default_timeout: float = 30.0):
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
        models: list[ProviderModel] = []
        for raw in payload.get("data", []):
            model_id = str(raw.get("id", "")).strip()
            if not model_id:
                continue
            metadata = public_metadata.get(model_id, {})
            endpoint_family = self._infer_endpoint_family(model_id, metadata)
            model = ProviderModel(
                id=model_id,
                provider=self.name,
                is_free=self._is_free_model(model_id, metadata),
                tags=self._tags_for_model(model_id),
                metadata={
                    "name": model_id,
                    "endpoint_family": endpoint_family,
                    "provider_metadata": metadata,
                },
            )
            models.append(model)
            self._metadata_cache[model_id] = metadata
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

    def _build_request(self, family: str, backend_model: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        messages = payload.get("messages", [])
        if family == "chat_completions":
            body = dict(payload)
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
        provider_npm = ((metadata.get("provider") or {}).get("npm") or "").lower()
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
        cost = metadata.get("cost") or {}
        numeric_values = [value for value in cost.values() if isinstance(value, (int, float))]
        return bool(numeric_values) and all(float(value) == 0.0 for value in numeric_values)

    @staticmethod
    def _tags_for_model(model_id: str) -> tuple[str, ...]:
        lowered = model_id.lower()
        tags: list[str] = []
        if any(token in lowered for token in ("code", "coder", "codex", "deepseek", "devstral", "qwen")):
            tags.append("coding")
        if any(token in lowered for token in ("mini", "nano", "flash", "haiku", "free")):
            tags.append("lightweight")
        if any(token in lowered for token in ("opus", "pro", "thinking", "reason", "large", "sonnet")):
            tags.append("heavyweight")
        return tuple(dict.fromkeys(tags))

    def _normalize_http_error(self, exc: HttpStatusError, *, backend_model: str) -> NormalizedProviderError:
        message = _extract_error_message(exc.details)
        lowered = message.lower()
        if "not supported for format" in lowered:
            return NormalizedProviderError("endpoint_family_mismatch", message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if "missing api key" in lowered:
            return NormalizedProviderError("endpoint_family_mismatch", message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if "insufficient balance" in lowered:
            return NormalizedProviderError("insufficient_balance", message, provider=self.name, backend_model=backend_model, retryable=False, details=exc.details)
        if exc.status_code in {401, 403}:
            return NormalizedProviderError("unauthorized", message or exc.message, provider=self.name, backend_model=backend_model, retryable=False, details=exc.details)
        if exc.status_code == 404:
            return NormalizedProviderError("model_missing", message or exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if exc.status_code == 429:
            return NormalizedProviderError("rate_limited", message or exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        if exc.status_code >= 500:
            return NormalizedProviderError("server_error", message or exc.message, provider=self.name, backend_model=backend_model, retryable=True, details=exc.details)
        return NormalizedProviderError("bad_request", message or exc.message, provider=self.name, backend_model=backend_model, retryable=False, details=exc.details)
