from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import NormalizedProviderError, ProviderChatResult, ProviderChatStreamEvent, ProviderModel
from hermes_router.providers.opencode_zen import OpencodeZenProvider
from hermes_router.service import RouterService
from hermes_router.state import SqliteStateStore


def make_config(tmp_path: Path, **overrides: Any) -> RouterConfig:
    state_dir = tmp_path / "state"
    base = RouterConfig(
        host="127.0.0.1",
        port=8788,
        log_level="info",
        api_key=None,
        cors_origins=(),
        default_timeout=30.0,
        inventory_ttl_seconds=300,
        refresh_interval_seconds=300,
        alias_model_limit=5,
        allow_direct_models=False,
        allow_models=(),
        block_models=(),
        state_dir=state_dir,
        db_path=state_dir / "router.db",
        debug_event_limit=50,
        rolling_window_seconds=3600.0,
        ranking_enabled=True,
        ranking_interval_seconds=900,
        ranking_worker_model=None,
        ranking_shortlist_size=5,
        provider_cooldown_seconds=300,
        provider_failure_threshold=3.0,
        provider_rate_limit_threshold=2.5,
        provider_timeout_threshold=2.5,
        provider_exhaustion_threshold=3.0,
        openrouter_api_key="secret",
        openrouter_base_url="https://openrouter.example/api/v1",
        openrouter_http_referer=None,
        openrouter_title=None,
        opencode_api_key="opencode-secret",
        opencode_base_url="https://opencode.example/api",
        assisted_bucket_model=None,
        assisted_bucket_batch_size=20,
        disabled_providers=(),
        disabled_models=(),
        provider_weight_overrides={},
        model_weight_overrides={},
        alias_pin_overrides={"auxiliary": (), "coding": (), "agentic": (), "vision": (), "tts": ()},
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free",)),
            AliasConfig(name="agentic", description="agent", preferred_models=("openrouter/agent-1:free",)),
            AliasConfig(name="vision", description="vision", preferred_models=("openrouter/vision-1:free",)),
            AliasConfig(name="tts", description="tts", preferred_models=("openrouter/audio-1:free",)),
        ),
    )
    return RouterConfig(**{**base.__dict__, **overrides})


def test_opencode_zen_enriches_models_from_openrouter_metadata(monkeypatch) -> None:
    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/api")

    def fake_request_json(method: str, path: str, timeout: float | None = None):
        assert method == "GET"
        assert path == "/models"
        return {"data": [{"id": "minimax-m2.5-free"}]}

    monkeypatch.setattr(provider.client, "request_json", fake_request_json)
    monkeypatch.setattr(provider, "_fetch_public_metadata", lambda timeout=None: {
        "minimax-m2.5-free": {"provider": {"npm": "@openrouter/openai"}, "cost": {"input": 0.0, "output": 0.0}}
    })
    monkeypatch.setattr(provider, "_fetch_openrouter_metadata", lambda timeout=None: {
        "by_id": {},
        "by_normalized": {
            "minimaxm25": [{
                "id": "minimax/minimax-m2.5:free",
                "name": "MiniMax M2.5",
                "description": "High-end coding model.",
                "created": 1774907286,
                "context_length": 200000,
                "modality": "text->text",
                "input_modalities": ["text"],
                "output_modalities": ["text"],
                "supported_parameters": ["tools", "tool_choice"],
            }]
        },
    })

    models = provider.list_models()

    assert len(models) == 1
    model = models[0]
    assert model.metadata["name"] == "MiniMax M2.5"
    assert model.metadata["description"] == "High-end coding model."
    assert model.metadata["created"] == 1774907286
    assert model.metadata["output_modalities"] == ["text"]
    assert model.metadata["supported_parameters"] == ["tools", "tool_choice"]
    assert model.metadata["openrouter_match_id"] == "minimax/minimax-m2.5:free"
    assert model.metadata["endpoint_family"] == "responses"


def test_config_reads_hermes_api_server_aliases(tmp_path: Path, monkeypatch) -> None:
    env_keys = (
        "GHOSTSHIP_ROUTER_HOST",
        "GHOSTSHIP_ROUTER_PORT",
        "GHOSTSHIP_ROUTER_API_KEY",
        "GHOSTSHIP_ROUTER_CORS_ORIGINS",
        "API_SERVER_HOST",
        "API_SERVER_PORT",
        "API_SERVER_KEY",
        "API_SERVER_CORS_ORIGINS",
        "GHOSTSHIP_ROUTER_STATE_DIR",
        "GHOSTSHIP_ROUTER_DB_PATH",
    )
    saved = {key: os.environ.get(key) for key in env_keys}
    try:
        for key in env_keys:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("API_SERVER_HOST", "0.0.0.0")
        monkeypatch.setenv("API_SERVER_PORT", "9999")
        monkeypatch.setenv("API_SERVER_KEY", "router-key")
        monkeypatch.setenv("API_SERVER_CORS_ORIGINS", "http://localhost:3000,https://example.test")
        monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path / "state"))
        config = RouterConfig.from_env()
        assert config.host == "0.0.0.0"
        assert config.port == 9999
        assert config.api_key == "router-key"
        assert config.cors_origins == ("http://localhost:3000", "https://example.test")
    finally:
        for key, value in saved.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)


def test_config_reads_opencode_go_api_key_alias(tmp_path: Path, monkeypatch) -> None:
    env_keys = (
        "OPENCODE_API_KEY",
        "OPENCODE_GO_API_KEY",
        "GHOSTSHIP_ROUTER_STATE_DIR",
        "GHOSTSHIP_ROUTER_DB_PATH",
    )
    saved = {key: os.environ.get(key) for key in env_keys}
    try:
        for key in env_keys:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "opencode-go-secret")
        monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path / "state"))
        config = RouterConfig.from_env()
        assert config.opencode_api_key == "opencode-go-secret"
    finally:
        for key, value in saved.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)


def test_config_reads_openai_api_key_for_custom_provider_compatibility(tmp_path: Path, monkeypatch) -> None:
    env_keys = (
        "GHOSTSHIP_ROUTER_API_KEY",
        "API_SERVER_KEY",
        "OPENAI_API_KEY",
        "GHOSTSHIP_ROUTER_STATE_DIR",
        "GHOSTSHIP_ROUTER_DB_PATH",
    )
    saved = {key: os.environ.get(key) for key in env_keys}
    try:
        for key in env_keys:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "custom-provider-key")
        monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path / "state"))
        config = RouterConfig.from_env()
        assert config.api_key == "custom-provider-key"
    finally:
        for key, value in saved.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)


class DummyProvider:
    def __init__(
        self,
        name: str,
        *,
        failures: dict[str, list[str]] | None = None,
        models: list[ProviderModel] | None = None,
        classification_payload: dict[str, Any] | None = None,
        first_text_latency_ms: float | None = 12.5,
        rerank_bare_ids: bool = False,
    ):
        self.name = name
        self.failures = {key: list(values) for key, values in (failures or {}).items()}
        self.calls: list[str] = []
        self.list_calls = 0
        self.first_text_latency_ms = first_text_latency_ms
        self.rerank_bare_ids = rerank_bare_ids
        self.models = models or [
            ProviderModel(id=f"{name}/light-1:free", provider=self.name, is_free=True, tags=("auxiliary",)),
            ProviderModel(id=f"{name}/code-1:free", provider=self.name, is_free=True, tags=("coding",), metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"]}),
            ProviderModel(id=f"{name}/agent-1:free", provider=self.name, is_free=True, tags=("agentic",), metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"]}),
            ProviderModel(id=f"{name}/vision-1:free", provider=self.name, is_free=True, tags=("vision",), metadata={"input_modalities": ["image"], "output_modalities": ["text"]}),
            ProviderModel(id=f"{name}/audio-1:free", provider=self.name, is_free=True, tags=("tts",), metadata={"output_modalities": ["audio"]}),
        ]
        default_rankings = []
        for model in self.models:
            default_rankings.append(
                {
                    "provider": model.provider,
                    "id": model.id,
                    "tags": list(model.tags),
                    "alias_scores": {
                        "auxiliary": 10 if "auxiliary" in model.tags else 1,
                        "coding": 10 if "coding" in model.tags else 1,
                        "agentic": 10 if "agentic" in model.tags else 1,
                        "vision": 10 if "vision" in model.tags else 1,
                        "tts": 10 if "tts" in model.tags else 1,
                    },
                    "reason": f"{model.id} ranked by dummy provider",
                    "confidence": 0.9,
                }
            )
        self.classification_payload = classification_payload or {"models": default_rankings}

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        self.list_calls += 1
        return list(self.models)

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        self.calls.append(backend_model)
        messages = payload.get("messages", [])
        system_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "system")
        user_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "user")
        if payload.get("temperature") == 0 and '"alias_scores"' in system_text:
            return ProviderChatResult(
                payload={
                    "id": "chatcmpl-classify",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": json.dumps(self.classification_payload)},
                            "finish_reason": "stop",
                        }
                    ],
                },
                provider=self.name,
                backend_model=backend_model,
                first_text_latency_ms=self.first_text_latency_ms,
            )
        if payload.get("temperature") == 0 and '"ordered"' in system_text:
            try:
                request = json.loads(user_text)
            except json.JSONDecodeError:
                request = {}
            alias = str(request.get("alias", "coding"))
            ordered = [
                (model.id if self.rerank_bare_ids else f"{model.provider}::{model.id}")
                for model in self.models
                if alias in model.tags or alias.split("-", 1)[0] in model.id
            ] or [
                (model.id if self.rerank_bare_ids else f"{model.provider}::{model.id}")
                for model in self.models
            ]
            return ProviderChatResult(
                payload={
                    "id": "chatcmpl-rerank",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": json.dumps({"alias": alias, "ordered": ordered, "reason": f"reranked for {alias}"})},
                            "finish_reason": "stop",
                        }
                    ],
                },
                provider=self.name,
                backend_model=backend_model,
                first_text_latency_ms=self.first_text_latency_ms,
            )
        queued = self.failures.get(backend_model)
        if queued:
            failure = queued.pop(0)
            raise NormalizedProviderError(
                failure,
                failure,
                provider=self.name,
                backend_model=backend_model,
                retryable=(failure != "bad_request" and failure != "insufficient_balance"),
            )
        return ProviderChatResult(
            payload={
                "id": "chatcmpl-demo",
                "object": "chat.completion",
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            },
            provider=self.name,
            backend_model=backend_model,
            first_text_latency_ms=self.first_text_latency_ms,
        )

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None):
        result = self.chat_completions(backend_model, payload, timeout=timeout)
        from hermes_router.providers.base import ProviderChatStreamResult, ProviderChatStreamState

        state = ProviderChatStreamState(
            first_text_latency_ms=result.first_text_latency_ms,
            usage=result.payload.get("usage") if isinstance(result.payload.get("usage"), dict) else None,
            final_payload=result.payload,
        )
        message = ((result.payload.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        tool_calls = message.get("tool_calls") if isinstance(message.get("tool_calls"), list) else None
        state.emitted_text = str(content)
        if isinstance(reasoning, str):
            state.emitted_reasoning = reasoning

        def chunks():
            if content or reasoning or tool_calls:
                delta: dict[str, Any] = {}
                if content:
                    delta["content"] = str(content)
                if isinstance(reasoning, str) and reasoning:
                    delta["reasoning_content"] = reasoning
                if tool_calls:
                    delta["tool_calls"] = tool_calls
                yield ProviderChatStreamEvent(
                    content=str(content) if content else None,
                    reasoning=reasoning if isinstance(reasoning, str) and reasoning else None,
                    tool_calls=tool_calls,
                    finish_reason=((result.payload.get("choices") or [{}])[0].get("finish_reason") or None),
                    usage=state.usage,
                    raw_chunk={
                        "id": result.payload.get("id") or "chatcmpl-demo",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": backend_model,
                        "choices": [{"index": 0, "delta": delta, "finish_reason": ((result.payload.get("choices") or [{}])[0].get("finish_reason") or None)}],
                    },
                )
            if state.usage:
                yield ProviderChatStreamEvent(
                    usage=state.usage,
                    raw_chunk={
                        "id": result.payload.get("id") or "chatcmpl-demo",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": backend_model,
                        "choices": [],
                        "usage": state.usage,
                    },
                )

        return ProviderChatStreamResult(chunks=chunks(), provider=self.name, backend_model=backend_model, state=state)


def test_models_endpoint_lists_aliases(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/v1/models")
        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload["data"]] == ["auxiliary", "coding", "agentic", "vision", "tts"]


def test_non_v1_models_alias_lists_aliases(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/models")
        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload["data"]] == ["auxiliary", "coding", "agentic", "vision", "tts"]


def test_health_endpoints_match_hermes_shape(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "platform": "ghostship-hermes-router"}
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "platform": "ghostship-hermes-router"}


def test_readyz_is_unready_without_providers(tmp_path: Path) -> None:
    config = make_config(tmp_path, openrouter_api_key=None, opencode_api_key=None)
    service = RouterService(config, providers={}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ok"] is False


def test_app_serves_with_persisted_routes_while_startup_refresh_runs(tmp_path: Path) -> None:
    config = make_config(tmp_path, refresh_interval_seconds=3600)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="persisted")

    original_refresh_inventory = service.refresh_inventory

    def slow_refresh_inventory(*, reason: str) -> list[ProviderModel]:
        time.sleep(0.5)
        return original_refresh_inventory(reason=reason)

    service.refresh_inventory = slow_refresh_inventory  # type: ignore[method-assign]

    started_at = time.monotonic()
    with TestClient(create_app(config=config, service=service)) as client:
        startup_elapsed = time.monotonic() - started_at
        assert startup_elapsed < 0.4
        response = client.get("/v1/models")
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["data"]] == ["auxiliary", "coding", "agentic", "vision", "tts"]


def test_readyz_waits_for_background_inventory_load_when_no_state_exists(tmp_path: Path) -> None:
    config = make_config(tmp_path, refresh_interval_seconds=3600)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    original_refresh_inventory = service.refresh_inventory

    def slow_refresh_inventory(*, reason: str) -> list[ProviderModel]:
        time.sleep(0.35)
        return original_refresh_inventory(reason=reason)

    service.refresh_inventory = slow_refresh_inventory  # type: ignore[method-assign]

    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ok"] is False
        models = client.get("/v1/models")
        assert models.status_code == 200
        time.sleep(0.5)
        ready = client.get("/readyz")
        assert ready.status_code == 200
        assert ready.json()["ok"] is True
        models = client.get("/v1/models")
        assert any(item["metadata"]["candidate_count"] > 0 for item in models.json()["data"])


def test_api_key_protects_router_api_endpoints(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="router-key")
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/v1/models")
        assert response.status_code == 401
        response = client.get("/v1/models", headers={"Authorization": "Bearer router-key"})
        assert response.status_code == 200
        response = client.get("/debug/state", headers={"Authorization": "Bearer router-key"})
        assert response.status_code == 200


def test_chat_completion_routes_alias(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/code-1:free"
        assert response.headers["x-ghostship-router-first-text-latency-ms"] == "12.5"


def test_non_v1_chat_completion_alias_routes_alias(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/code-1:free"


def test_chat_completion_fails_over_to_next_model(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "openrouter/heavy-1:free")),
            AliasConfig(name="vision", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "heavy-1:free"


def test_chat_completion_fails_over_across_providers_at_model_level(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    opencode = DummyProvider(
        "opencode-zen",
        models=[
            ProviderModel(id="qwen3-coder:free", provider="opencode-zen", is_free=True, tags=("coding",)),
            ProviderModel(id="gpt-5-nano:free", provider="opencode-zen", is_free=True, tags=("auxiliary",)),
        ],
        first_text_latency_ms=8.0,
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "opencode/qwen3-coder:free")),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(
        config,
        providers={"openrouter": openrouter, "opencode-zen": opencode},
        state_store=SqliteStateStore(config.db_path),
    )
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-provider"] == "opencode-zen"
        assert response.headers["x-ghostship-router-backend-model"] == "qwen3-coder:free"


def test_paid_models_are_not_routable(tmp_path: Path) -> None:
    provider = DummyProvider(
        "opencode-zen",
        models=[ProviderModel(id="qwen3-coder", provider="opencode-zen", is_free=False, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        openrouter_api_key=None,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("opencode/qwen3-coder",)),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"opencode-zen": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 503
        assert service.preview_routes("coding") == []


def test_models_without_tool_support_are_not_routable(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/lyria-3-pro-preview",
                provider="openrouter",
                is_free=True,
                tags=("vision",),
                metadata={
                    "output_modalities": ["text", "audio"],
                    "supported_parameters": ["max_tokens", "temperature"],
                    "created": 1774907286,
                },
            )
        ],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    assert service.preview_routes("vision") == []


def test_agentic_requires_tool_support(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="agent-plain:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"output_modalities": ["text"], "supported_parameters": ["max_tokens"]},
            )
        ],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    assert service.preview_routes("agentic") == []


def test_music_audio_models_are_not_routable_for_tts(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/lyria-3-pro-preview",
                provider="openrouter",
                is_free=True,
                tags=("tts",),
                metadata={
                    "name": "Google: Lyria 3 Pro Preview",
                    "description": "Music generation model with lyrics and full instrumental arrangements.",
                    "output_modalities": ["text", "audio"],
                    "created": 1774907286,
                },
            )
        ],
    )
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    assert service.preview_routes("tts") == []


def test_primary_alias_prefers_higher_coding_score_over_auxiliary_tag(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="minimax/minimax-m2.5:free",
                provider="openrouter",
                is_free=True,
                tags=("auxiliary",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    target = next(model for model in service._inventory_for_all() if model.id == "minimax/minimax-m2.5:free")
    assert service._primary_alias_for_model(target) == "coding"


def test_family_match_prefers_primary_id_over_description_fallback(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="qwen/qwen3.6-plus:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={
                    "name": "Qwen 3.6 Plus",
                    "description": "Benchmarked against Nemotron and GPT-OSS families for coding.",
                    "supported_parameters": ["tools", "tool_choice"],
                    "output_modalities": ["text"],
                    "created": 1774907286,
                },
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview[0]["family_name"] == "qwen"


def test_coding_family_bias_prefers_minimax_over_qwen_when_capabilities_are_close(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="minimax/minimax-m2.5:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="qwen/qwen3.6-plus:free",
                provider="openrouter",
                is_free=True,
                tags=(),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview[0]["backend_model"] == "minimax/minimax-m2.5:free"
    assert preview[0]["family_name"] == "minimax"
    qwen = next(item for item in preview if item["backend_model"] == "qwen/qwen3.6-plus:free")
    assert preview[0]["family_bias"] > qwen["family_bias"]


def test_coding_subfamily_penalty_does_not_drag_qwen_below_glm(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="qwen/qwen3.6-plus:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="qwen/qwen3-next-80b-a3b-instruct:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1770000000},
            ),
            ProviderModel(
                id="z-ai/glm-4.5-air:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1740000000},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    qwen = next(item for item in preview if item["backend_model"] == "qwen/qwen3.6-plus:free")
    glm = next(item for item in preview if item["backend_model"] == "z-ai/glm-4.5-air:free")
    assert qwen["parameter_bias"] >= 0.0
    assert qwen["total_score"] > glm["total_score"]


def test_coding_penalizes_smaller_family_variants_when_larger_peer_exists(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/gemini-3.1-flash-lite:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="google/gemini-3.1-pro:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert [item["backend_model"] for item in preview[:2]] == [
        "google/gemini-3.1-pro:free",
        "google/gemini-3.1-flash-lite:free",
    ]
    assert preview[0]["parameter_bias"] == 0.0
    assert preview[1]["parameter_bias"] < 0.0


def test_agentic_penalizes_trinity_mini_below_qwen(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="arcee-ai/trinity-large-preview:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1770000000},
            ),
            ProviderModel(
                id="arcee-ai/trinity-mini:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1770000000},
            ),
            ProviderModel(
                id="qwen/qwen3.6-plus:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("agentic")
    ordered = [item["backend_model"] for item in preview[:3]]
    assert ordered == [
        "arcee-ai/trinity-large-preview:free",
        "qwen/qwen3.6-plus:free",
        "arcee-ai/trinity-mini:free",
    ]
    trinity_mini = next(item for item in preview if item["backend_model"] == "arcee-ai/trinity-mini:free")
    qwen = next(item for item in preview if item["backend_model"] == "qwen/qwen3.6-plus:free")
    assert trinity_mini["parameter_bias"] < qwen["parameter_bias"]


def test_agentic_family_bias_prefers_gemini_over_trinity_and_minimax(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/gemini-3.1-pro:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="arcee-ai/trinity-large-preview:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="minimax/minimax-m2.5:free",
                provider="openrouter",
                is_free=True,
                tags=("agentic",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("agentic")
    assert [item["backend_model"] for item in preview[:3]] == [
        "google/gemini-3.1-pro:free",
        "arcee-ai/trinity-large-preview:free",
        "minimax/minimax-m2.5:free",
    ]


def test_vision_parameter_bias_prefers_larger_gemma_model(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/gemma-3-4b-it:free",
                provider="openrouter",
                is_free=True,
                tags=("vision",),
                metadata={"input_modalities": ["text", "image"], "output_modalities": ["text"], "created": 1741905510},
            ),
            ProviderModel(
                id="google/gemma-3-12b-it:free",
                provider="openrouter",
                is_free=True,
                tags=("vision",),
                metadata={"input_modalities": ["text", "image"], "output_modalities": ["text"], "created": 1741902625},
            ),
            ProviderModel(
                id="google/gemma-3-27b-it:free",
                provider="openrouter",
                is_free=True,
                tags=("vision",),
                metadata={"input_modalities": ["text", "image"], "output_modalities": ["text"], "created": 1741756359},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("vision")
    assert [item["backend_model"] for item in preview[:3]] == [
        "google/gemma-3-27b-it:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-4b-it:free",
    ]
    assert preview[0]["parameter_count_b"] == 27.0
    assert preview[0]["parameter_bias"] > preview[1]["parameter_bias"] > preview[2]["parameter_bias"]
    assert preview[0]["size_rank_bonus"] > preview[1]["size_rank_bonus"] > preview[2]["size_rank_bonus"]


def test_auxiliary_prefers_smaller_models_when_family_fit_is_close(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/gemma-3-4b-it:free",
                provider="openrouter",
                is_free=True,
                tags=("auxiliary",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
            ProviderModel(
                id="google/gemma-3-27b-it:free",
                provider="openrouter",
                is_free=True,
                tags=("auxiliary",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("auxiliary")
    assert [item["backend_model"] for item in preview[:2]] == [
        "google/gemma-3-4b-it:free",
        "google/gemma-3-27b-it:free",
    ]
    assert preview[0]["parameter_bias"] > preview[1]["parameter_bias"]


def test_size_penalty_requires_a_larger_family_peer(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="google/gemini-3.1-flash-lite:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="aux", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="agentic", description="agent", preferred_models=()),
            AliasConfig(name="vision", description="vision", preferred_models=()),
            AliasConfig(name="tts", description="tts", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview[0]["parameter_bias"] == 0.0


def test_recency_bias_prefers_newer_models_when_other_scores_tie(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(
                id="qwen/qwen3-old-coder:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1700000000},
            ),
            ProviderModel(
                id="qwen/qwen3-new-coder:free",
                provider="openrouter",
                is_free=True,
                tags=("coding",),
                metadata={"supported_parameters": ["tools", "tool_choice"], "output_modalities": ["text"], "created": 1774907286},
            ),
        ],
    )
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview[0]["backend_model"] == "qwen/qwen3-new-coder:free"
    ranking = service.debug_rankings("coding")
    newer = next(item for item in ranking["candidates"] if item["backend_model"] == "qwen/qwen3-new-coder:free")
    older = next(item for item in ranking["candidates"] if item["backend_model"] == "qwen/qwen3-old-coder:free")
    assert newer["recency_bias"] > older["recency_bias"]


def test_openrouter_prefixed_pins_normalize_to_backend_model_ids(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[ProviderModel(id="qwen/qwen3-coder:free", provider="openrouter", is_free=True, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/qwen/qwen3-coder:free",)),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert [candidate["backend_model"] for candidate in preview] == ["qwen/qwen3-coder:free"]

    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-provider"] == "openrouter"
        assert response.headers["x-ghostship-router-backend-model"] == "qwen/qwen3-coder:free"
        assert provider.calls
        assert all(call == "qwen/qwen3-coder:free" for call in provider.calls)


def test_model_missing_triggers_refresh(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["model_missing"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "openrouter/heavy-1:free")),
            AliasConfig(name="vision", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    before = provider.list_calls
    _, headers = service.chat_completions(ChatCompletionRequest.model_validate({"model": "coding", "messages": [{"role": "user", "content": "hello"}]}))
    assert provider.list_calls == before + 1
    assert headers["X-Ghostship-Router-Backend-Model"] == "heavy-1:free"


def test_refresh_persists_inventory_across_service_restart(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter")
    opencode = DummyProvider(
        "opencode-zen",
        models=[ProviderModel(id="qwen3-coder", provider="opencode-zen", is_free=False, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    store = SqliteStateStore(config.db_path)
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=store)
    service.refresh_inventory(reason="manual")
    restarted = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    preview = restarted.preview_routes("coding")
    assert any(candidate["backend_model"] == "openrouter/code-1:free" for candidate in preview)
    assert all(candidate["backend_model"] != "qwen3-coder" for candidate in preview)
    assert restarted.debug_model("opencode-zen", "qwen3-coder")["inventory"]["is_free"] is False


def test_ranking_prefers_opencode_worker_and_persists_rankings(tmp_path: Path) -> None:
    openrouter = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(id="assistant-free:free", provider="openrouter", is_free=True, tags=("auxiliary",)),
            ProviderModel(id="demo/code-1:free", provider="openrouter", is_free=True, tags=("coding",)),
        ],
    )
    opencode = DummyProvider(
        "opencode-zen",
        models=[
            ProviderModel(id="gpt-5-nano", provider="opencode-zen", is_free=True, tags=("auxiliary",)),
            ProviderModel(id="qwen3-coder:free", provider="opencode-zen", is_free=True, tags=("coding",)),
        ],
        classification_payload={
            "models": [
                {
                    "provider": "openrouter",
                    "id": "demo/code-1:free",
                    "tags": ["coding"],
                    "alias_scores": {"auxiliary": 1, "coding": 11, "vision": 0},
                    "reason": "best coder model",
                    "confidence": 0.94,
                },
                {
                    "provider": "opencode-zen",
                    "id": "qwen3-coder:free",
                    "tags": ["coding"],
                    "alias_scores": {"auxiliary": 1, "coding": 12, "vision": 0},
                    "reason": "best opencode coder model",
                    "confidence": 0.97,
                },
            ]
        },
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    state = service.debug_state()
    assert state["last_ranking_worker"]["provider_name"] == "opencode-zen"
    assert state["last_ranking_worker"]["backend_model"] == "gpt-5-nano"
    assert "gpt-5-nano" in opencode.calls
    assert state["state"]["ranking_count"] >= 2
    ranking = service.debug_rankings("coding")
    assert any(candidate["backend_model"] == "qwen3-coder:free" and candidate["learned_ranking_score"] > 0 for candidate in ranking["candidates"])


def test_debug_endpoints_return_state_and_events(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        state = client.get("/debug/state")
        events = client.get("/debug/events")
        assert state.status_code == 200
        assert events.status_code == 200
        assert state.json()["state"]["event_count"] >= 1
        assert state.json()["state"]["model_state"][0]["last_first_text_latency_ms"] == 12.5
        assert len(events.json()) >= 1


def test_metrics_endpoint_exposes_request_failover_and_candidate_metrics(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "openrouter/heavy-1:free")),
            AliasConfig(name="vision", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "ghostship_router_requests_total" in metrics.text
        assert 'alias="coding"' in metrics.text
        assert "ghostship_router_failovers_total 1" in metrics.text
        assert "ghostship_router_candidate_count" in metrics.text


def test_provider_cooldown_suppresses_provider_after_broad_failures(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    opencode = DummyProvider(
        "opencode-zen",
        models=[ProviderModel(id="qwen3-coder:free", provider="opencode-zen", is_free=True, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        provider_rate_limit_threshold=1.0,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "opencode/qwen3-coder:free")),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    _, headers = service.chat_completions(ChatCompletionRequest.model_validate({"model": "coding", "messages": [{"role": "user", "content": "hello"}]}))
    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    providers = service.debug_providers()
    openrouter_state = next(item for item in providers if item["provider_name"] == "openrouter")
    assert openrouter_state["cooldown_until"] > 0
    preview = service.preview_routes("coding")
    assert preview[0]["provider_name"] == "opencode-zen"


def test_ranking_tolerates_bare_model_ids_from_worker(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", rerank_bare_ids=True)
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("auxiliary")
    assert preview
    assert service.debug_state()["last_ranking_error"] is None


def test_overrides_survive_restart_and_affect_routing(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter")
    opencode = DummyProvider(
        "opencode-zen",
        models=[ProviderModel(id="qwen3-coder:free", provider="opencode-zen", is_free=True, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    store = SqliteStateStore(config.db_path)
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=store)
    service.refresh_inventory(reason="manual")
    store.upsert_provider_override("openrouter", enabled=False)
    store.upsert_alias_pin("coding", ("opencode/qwen3-coder:free",))
    restarted = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    preview = restarted.preview_routes("coding")
    assert preview[0]["provider_name"] == "opencode-zen"
    provider_debug = next(item for item in restarted.debug_providers() if item["provider_name"] == "openrouter")
    assert provider_debug["override"]["enabled"] is False


def test_heuristic_ordering_still_works_without_ranking_data(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(
        tmp_path,
        ranking_enabled=False,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview
    assert preview[0]["backend_model"] == "openrouter/code-1:free"


def test_empty_inventory_does_not_trigger_lazy_refresh(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="auxiliary", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="vision", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    assert service.preview_routes("coding") == []
    assert provider.list_calls == 0
    assert service.readiness().ok is False


def test_config_defaults_state_dir_to_user_state_home(monkeypatch) -> None:
    monkeypatch.delenv("GHOSTSHIP_ROUTER_STATE_DIR", raising=False)
    monkeypatch.delenv("GHOSTSHIP_ROUTER_DB_PATH", raising=False)
    monkeypatch.setenv("HOME", "/tmp/router-home")
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    config = RouterConfig.from_env()
    assert config.state_dir == Path("/tmp/router-home/.local/state/ghostship-hermes/router")
    assert config.db_path == Path("/tmp/router-home/.local/state/ghostship-hermes/router/router.db")


def test_config_prefers_xdg_state_home(monkeypatch) -> None:
    monkeypatch.delenv("GHOSTSHIP_ROUTER_STATE_DIR", raising=False)
    monkeypatch.delenv("GHOSTSHIP_ROUTER_DB_PATH", raising=False)
    monkeypatch.setenv("HOME", "/tmp/router-home")
    monkeypatch.setenv("XDG_STATE_HOME", "/tmp/router-xdg")
    config = RouterConfig.from_env()
    assert config.state_dir == Path("/tmp/router-xdg/ghostship-hermes/router")
    assert config.db_path == Path("/tmp/router-xdg/ghostship-hermes/router/router.db")


def test_health_endpoints_match_hermes_shape(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        health = client.get("/health")
        v1_health = client.get("/v1/health")
        assert health.status_code == 200
        assert v1_health.status_code == 200
        assert health.json()["status"] == "ok"
        assert v1_health.json()["status"] == "ok"
        assert health.headers["x-content-type-options"] == "nosniff"


def test_chat_completion_stream_returns_sse_and_session_header(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "coding", "messages": [{"role": "user", "content": "hello"}], "stream": True},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers["x-hermes-session-id"]
        assert "chat.completion.chunk" in response.text
        assert "data: [DONE]" in response.text
        assert "ok" in response.text


def test_chat_completion_stream_preserves_tool_calls_and_reasoning(tmp_path: Path) -> None:
    class ToolProvider(DummyProvider):
        def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
            self.calls.append(backend_model)
            return ProviderChatResult(
                payload={
                    "id": "chatcmpl-tool",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "reasoning_content": "thinking",
                                "tool_calls": [
                                    {
                                        "id": "call_demo",
                                        "type": "function",
                                        "function": {"name": "terminal", "arguments": "{\"cmd\":\"pwd\"}"},
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                },
                provider=self.name,
                backend_model=backend_model,
                first_text_latency_ms=self.first_text_latency_ms,
            )

    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": ToolProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "coding", "messages": [{"role": "user", "content": "use a tool"}], "stream": True},
        )
        assert response.status_code == 200
        assert "\"reasoning_content\": \"thinking\"" in response.text
        assert "\"tool_calls\"" in response.text
        assert "\"finish_reason\": \"tool_calls\"" in response.text
        assert "\"usage\"" in response.text


def test_chat_completion_session_header_reuses_stored_history(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        first = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "first"}]})
        session_id = first.headers["x-hermes-session-id"]
        second = client.post(
            "/v1/chat/completions",
            headers={"X-Hermes-Session-Id": session_id},
            json={
                "model": "coding",
                "messages": [
                    {"role": "user", "content": "ignored-old"},
                    {"role": "assistant", "content": "ignored-answer"},
                    {"role": "user", "content": "second"},
                ],
            },
        )
        assert second.status_code == 200
        session_messages = service.state_store.load_chat_session(session_id)
        assert session_messages[0]["content"] == "first"
        assert session_messages[-2]["content"] == "second"


def test_responses_create_get_delete_and_chain_previous_response(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        create = client.post("/v1/responses", json={"input": "What is 1+1?", "instructions": "Be terse."})
        assert create.status_code == 200
        created = create.json()
        response_id = created["id"]
        assert created["object"] == "response"
        assert created["output"][0]["content"][0]["type"] == "output_text"

        fetched = client.get(f"/v1/responses/{response_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == response_id

        chained = client.post("/v1/responses", json={"input": "And 1 more?", "previous_response_id": response_id})
        assert chained.status_code == 200
        chained_id = chained.json()["id"]
        stored = service.state_store.get_response(chained_id)
        assert stored is not None
        assert stored["instructions"] == "Be terse."
        assert any(message["role"] == "assistant" for message in stored["conversation_history"])

        deleted = client.delete(f"/v1/responses/{response_id}")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True
        missing = client.get(f"/v1/responses/{response_id}")
        assert missing.status_code == 404


def test_non_v1_responses_aliases_work(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        create = client.post("/responses", json={"input": "What is 1+1?", "instructions": "Be terse."})
        assert create.status_code == 200
        response_id = create.json()["id"]
        fetched = client.get(f"/responses/{response_id}")
        assert fetched.status_code == 200
        deleted = client.delete(f"/responses/{response_id}")
        assert deleted.status_code == 200


def test_responses_stream_returns_openai_events_and_completed_payload(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/responses",
            json={
                "input": "Hello",
                "stream": True,
                "tools": [{"type": "function", "name": "terminal", "description": "run", "parameters": {"type": "object"}}],
                "tool_choice": "auto",
                "parallel_tool_calls": True,
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "event: response.created" in response.text
        assert "event: response.output_item.added" in response.text
        assert "event: response.content_part.added" in response.text
        assert "event: response.output_text.delta" in response.text
        assert "event: response.completed" in response.text
        completed_line = [line for line in response.text.splitlines() if line.startswith("data: {\"response\":")][-1]
        payload = json.loads(completed_line[6:])
        assert payload["response"]["parallel_tool_calls"] is True
        assert payload["response"]["tool_choice"] == "auto"
        assert payload["response"]["tools"][0]["name"] == "terminal"
        assert payload["response"]["output"][0]["type"] == "message"


def test_responses_stream_preserves_function_call_items(tmp_path: Path) -> None:
    class ToolProvider(DummyProvider):
        def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
            self.calls.append(backend_model)
            return ProviderChatResult(
                payload={
                    "id": "chatcmpl-tool",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_demo",
                                        "type": "function",
                                        "function": {"name": "terminal", "arguments": "{\"cmd\":\"pwd\"}"},
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                },
                provider=self.name,
                backend_model=backend_model,
                first_text_latency_ms=self.first_text_latency_ms,
            )

    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": ToolProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/responses",
            json={
                "input": "use a tool",
                "stream": True,
                "tools": [{"type": "function", "name": "terminal", "description": "run", "parameters": {"type": "object"}}],
            },
        )
        assert response.status_code == 200
        assert "event: response.function_call_arguments.delta" in response.text
        completed_line = [line for line in response.text.splitlines() if line.startswith("data: {\"response\":")][-1]
        payload = json.loads(completed_line[6:])
        function_item = next(item for item in payload["response"]["output"] if item["type"] == "function_call")
        assert function_item["name"] == "terminal"
        assert function_item["call_id"] == "call_demo"


def test_responses_conversation_name_tracks_latest_response(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    with TestClient(create_app(config=config, service=service)) as client:
        first = client.post("/v1/responses", json={"input": "hello", "conversation": "demo"})
        second = client.post("/v1/responses", json={"input": "again", "conversation": "demo"})
        assert first.status_code == 200
        assert second.status_code == 200
        assert service.state_store.get_conversation_response("demo") == second.json()["id"]


def test_auth_protects_openai_endpoints_but_not_health(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="sk-test")
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/v1/models").status_code == 401
        authorized = client.get("/v1/models", headers={"Authorization": "Bearer sk-test"})
        assert authorized.status_code == 200


def test_invalid_json_returns_openai_style_error(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/chat/completions",
            data="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert "error" in response.json()
