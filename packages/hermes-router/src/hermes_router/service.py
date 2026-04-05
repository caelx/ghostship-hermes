from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from .config import AliasConfig, RouterConfig
from .models import ChatCompletionRequest, ModelCard, ModelsResponse, ReadinessResponse
from .providers.base import ChatProvider, NormalizedProviderError, ProviderModel
from .providers.opencode_zen import OpencodeZenProvider
from .providers.openrouter import OpenRouterProvider
from .state import RouteEvent, SqliteStateStore, StateStore

logger = logging.getLogger("hermes_router")

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
    is_fallback: bool = False


class RouterService:
    def __init__(self, config: RouterConfig, *, providers: dict[str, ChatProvider] | None = None, state_store: StateStore | None = None):
        self.config = config
        self.state_store = state_store or SqliteStateStore(config.db_path)
        self.providers = providers if providers is not None else self._build_providers()
        self._provider_names = tuple(sorted(self.providers.keys()))
        self._inventory = self._load_persisted_inventory()
        self._inventory_loaded_at = 0.0
        self._last_refresh_reason = "persisted"
        self._last_refresh_at = 0.0
        self._last_refresh_error: dict[str, Any] | None = None
        self._last_bucket_model: str | None = None

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

    def chat_completions(self, request: ChatCompletionRequest) -> tuple[dict[str, Any], dict[str, str]]:
        if request.stream:
            raise RouterServiceError(501, {"message": "Streaming chat completions are not implemented yet."})
        candidates = self._resolve_candidates(request.model)
        if not candidates:
            raise RouterServiceError(503, {"message": f"No route candidates are available for alias '{request.model}'."})

        request_payload = request.model_dump(mode="json", exclude_none=True)
        request_payload.pop("timeout", None)
        errors: list[dict[str, Any]] = []
        for candidate in candidates:
            provider = self.providers.get(candidate.provider_name)
            if provider is None:
                continue
            start = time.monotonic()
            try:
                result = provider.chat_completions(candidate.backend_model, request_payload, timeout=request.timeout or self.config.default_timeout)
                latency_ms = round((time.monotonic() - start) * 1000, 2)
                first_text_latency_ms = result.first_text_latency_ms or latency_ms
                self.state_store.apply_success(
                    candidate.provider_name,
                    candidate.backend_model,
                    latency_ms=latency_ms,
                    first_text_latency_ms=first_text_latency_ms,
                )
                self.state_store.record_attempt(
                    RouteEvent(
                        alias=request.model,
                        provider_name=candidate.provider_name,
                        backend_model=candidate.backend_model,
                        success=True,
                        retryable=False,
                        is_fallback=False,
                        category=None,
                        latency_ms=latency_ms,
                        first_text_latency_ms=first_text_latency_ms,
                        details={"result_provider": result.provider},
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
                logger.warning(
                    "router candidate failed: provider=%s backend_model=%s category=%s retryable=%s",
                    exc.provider,
                    exc.backend_model,
                    exc.category,
                    exc.retryable,
                )
                self.state_store.apply_failure(candidate.provider_name, candidate.backend_model, category=exc.category, retryable=exc.retryable)
                self.state_store.record_attempt(
                    RouteEvent(
                        alias=request.model,
                        provider_name=candidate.provider_name,
                        backend_model=candidate.backend_model,
                        success=False,
                        retryable=exc.retryable,
                        is_fallback=False,
                        category=exc.category,
                        latency_ms=latency_ms,
                        first_text_latency_ms=None,
                        details=exc.details,
                        created_at=time.time(),
                    )
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
                if not exc.retryable:
                    continue

        raise RouterServiceError(
            503,
            {
                "message": f"All route candidates failed for alias '{request.model}'.",
                "attempts": errors,
            },
        )

    def refresh_inventory(self, *, reason: str) -> list[ProviderModel]:
        refreshed: list[ProviderModel] = []
        errors: dict[str, Any] = {}
        for provider_name, provider in self.providers.items():
            try:
                models = provider.list_models(timeout=self.config.default_timeout)
                refreshed.extend(models)
                self.state_store.save_inventory(provider_name, models, reason=reason)
            except NormalizedProviderError as exc:
                errors[provider_name] = {"category": exc.category, "details": exc.details}
        classifications = self._classify_inventory_with_free_model(refreshed)
        if classifications:
            self.state_store.save_classifications(classifications, source=self.config.assisted_bucket_model or "free-model")
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
            self._log_event("refresh_complete", reason=reason, model_count=len(self._inventory), classifications=len(classifications))
        return self._inventory

    def debug_state(self) -> dict[str, Any]:
        return {
            "providers": list(self._provider_names),
            "last_refresh_reason": self._last_refresh_reason,
            "last_refresh_at": self._last_refresh_at,
            "last_refresh_error": self._last_refresh_error,
            "assisted_bucket_model": self._last_bucket_model,
            "inventory_ttl_seconds": self.config.inventory_ttl_seconds,
            "refresh_interval_seconds": self.config.refresh_interval_seconds,
            "state": self.state_store.snapshot(),
        }

    def debug_events(self) -> list[dict[str, Any]]:
        return self.state_store.get_recent_events(self.config.debug_event_limit)

    def preview_routes(self, alias: str) -> list[dict[str, Any]]:
        try:
            candidates = self._resolve_candidates(alias)
        except RouterServiceError:
            return []
        model_state = self.state_store.get_model_state()
        preview: list[dict[str, Any]] = []
        for candidate in candidates:
            state = model_state.get(f"{candidate.provider_name}::{candidate.backend_model}", {})
            preview.append(
                {
                    "provider_name": candidate.provider_name,
                    "backend_model": candidate.backend_model,
                    "is_free": self._model_is_free(candidate.provider_name, candidate.backend_model),
                    "cooldown_until": state.get("cooldown_until", 0),
                    "success_count": state.get("success_count", 0),
                    "failure_count": state.get("failure_count", 0),
                    "last_latency_ms": state.get("last_latency_ms"),
                    "last_first_text_latency_ms": state.get("last_first_text_latency_ms"),
                }
            )
        return preview

    def _resolve_candidates(self, alias: str) -> list[RouteCandidate]:
        alias_config = self.config.alias_map().get(alias)
        if alias_config is None:
            direct_candidates = self._resolve_direct_model(alias)
            if direct_candidates:
                return direct_candidates
            raise RouterServiceError(404, {"message": f"Unknown logical model alias '{alias}'."})

        candidates = self._preferred_candidates(alias_config.preferred_models)
        if not candidates:
            candidates = [RouteCandidate(provider_name=model.provider, backend_model=model.id) for model in self._discover_alias_candidates(alias_config)]
        return candidates

    def _resolve_direct_model(self, model_name: str) -> list[RouteCandidate]:
        if not self.config.allow_direct_models:
            return []
        return self._preferred_candidates((model_name,))

    def _preferred_candidates(self, model_ids: tuple[str, ...], *, inventory: list[ProviderModel] | None = None) -> list[RouteCandidate]:
        candidates: list[RouteCandidate] = []
        known_inventory = inventory if inventory is not None else self._inventory_for_all()
        for model_id in model_ids:
            if not self._model_allowed(model_id):
                continue
            normalized = model_id.removeprefix("opencode/")
            matched = [
                model
                for model in known_inventory
                if model.id == normalized or model.id == model_id
            ]
            if not matched and normalized == model_id and "openrouter" in self.providers:
                matched.append(ProviderModel(id=model_id, provider="openrouter", is_free=model_id.endswith(":free")))
            for model in matched:
                if self._is_cooling_down(model.provider, model.id):
                    continue
                candidate = RouteCandidate(provider_name=model.provider, backend_model=model.id)
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _discover_alias_candidates(self, alias: AliasConfig) -> list[ProviderModel]:
        filtered = [
            model
            for model in self._inventory_for_all()
            if self._model_allowed(model.id)
            and not self._is_cooling_down(model.provider, model.id)
        ]
        scored = sorted(filtered, key=lambda model: self._score_model(alias.name, model), reverse=True)
        return [model for model in scored if self._score_model(alias.name, model) > 0][: self.config.alias_model_limit]

    def _inventory_for_all(self) -> list[ProviderModel]:
        if not self._inventory:
            self.refresh_inventory(reason="lazy")
        return list(self._inventory)

    def _model_allowed(self, model_id: str) -> bool:
        normalized = model_id.removeprefix("opencode/")
        if self.config.allow_models and normalized not in self.config.allow_models and model_id not in self.config.allow_models:
            return False
        if normalized in self.config.block_models or model_id in self.config.block_models:
            return False
        return True

    def _model_is_free(self, provider_name: str, backend_model: str, *, inventory: list[ProviderModel] | None = None) -> bool:
        for model in (inventory if inventory is not None else self._inventory_for_all()):
            if model.provider == provider_name and model.id == backend_model:
                return model.is_free
        return False

    def _score_model(self, alias: str, model: ProviderModel) -> int:
        lowered = model.id.lower()
        state = self.state_store.get_model_state().get(f"{model.provider}::{model.id}", {})
        score = 1 + (100 if model.is_free else 0)
        if model.provider == "openrouter":
            score += 2
        for token in _ALIAS_HINTS.get(alias, ()):
            if token in lowered:
                score += 4
        for token in model.tags:
            if token == alias:
                score += 3
        for token in _ALIAS_PENALTIES.get(alias, ()):
            if token in lowered:
                score -= 3
        score += int(state.get("success_count", 0))
        score -= int(state.get("failure_count", 0))
        latency = state.get("last_first_text_latency_ms") or state.get("last_latency_ms")
        if latency:
            score -= int(float(latency) / 1000)
        return score

    def _is_cooling_down(self, provider_name: str, backend_model: str) -> bool:
        state = self.state_store.get_model_state().get(f"{provider_name}::{backend_model}", {})
        return float(state.get("cooldown_until", 0) or 0) > time.time()

    def _classify_inventory_with_free_model(self, models: list[ProviderModel]) -> dict[str, tuple[str, ...]]:
        model_id = self.config.assisted_bucket_model
        if not model_id:
            self._last_bucket_model = None
            return {}
        assisted_candidates = self._preferred_candidates((model_id,), inventory=models)
        if not assisted_candidates:
            self._last_bucket_model = None
            return {}
        candidate = assisted_candidates[0]
        if not self._model_is_free(candidate.provider_name, candidate.backend_model, inventory=models) and not candidate.backend_model.endswith(":free"):
            self._last_bucket_model = None
            return {}
        provider = self.providers.get(candidate.provider_name)
        if provider is None:
            self._last_bucket_model = None
            return {}
        targets = [model for model in models if model.is_free][: self.config.assisted_bucket_batch_size]
        if not targets:
            self._last_bucket_model = None
            return {}
        prompt = {
            "messages": [
                {
                    "role": "system",
                    "content": "Classify each model into zero or more aliases from lightweight, coding, heavyweight. Return JSON only in the shape {\"classifications\": [{\"id\": \"...\", \"tags\": [\"...\"]}]}",
                },
                {
                    "role": "user",
                    "content": "\n".join(model.id for model in targets),
                },
            ],
            "temperature": 0,
        }
        try:
            result = provider.chat_completions(candidate.backend_model, prompt, timeout=min(self.config.default_timeout, 20.0))
        except NormalizedProviderError as exc:
            self._log_event("classification_failed", category=exc.category)
            self._last_bucket_model = None
            return {}
        content = result.payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        self._last_bucket_model = candidate.backend_model
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return {}
        classifications: dict[str, tuple[str, ...]] = {}
        for item in payload.get("classifications", []):
            item_id = str(item.get("id", "")).strip()
            tags = tuple(tag for tag in item.get("tags", []) if tag in {"lightweight", "coding", "heavyweight"})
            if item_id and tags:
                classifications[item_id] = tags
        return classifications

    def _log_event(self, event: str, **fields: Any) -> None:
        logger.info("router_event %s", json.dumps({"event": event, **fields}, sort_keys=True))
