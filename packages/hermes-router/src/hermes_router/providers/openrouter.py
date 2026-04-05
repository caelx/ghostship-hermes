from __future__ import annotations

from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, TimeoutError, TransportError

from .base import NormalizedProviderError, ProviderChatResult, ProviderModel


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
