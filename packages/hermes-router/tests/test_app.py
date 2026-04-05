from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import NormalizedProviderError, ProviderChatResult, ProviderModel
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
        openrouter_api_key="secret",
        openrouter_base_url="https://openrouter.example/api/v1",
        openrouter_http_referer=None,
        openrouter_title=None,
        opencode_api_key="opencode-secret",
        opencode_base_url="https://opencode.example/api",
        assisted_bucket_model=None,
        assisted_bucket_batch_size=20,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free",)),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    return RouterConfig(**{**base.__dict__, **overrides})


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


class DummyProvider:
    def __init__(
        self,
        name: str,
        *,
        failures: dict[str, list[str]] | None = None,
        models: list[ProviderModel] | None = None,
        classification_payload: dict[str, Any] | None = None,
        first_text_latency_ms: float | None = 12.5,
    ):
        self.name = name
        self.failures = {key: list(values) for key, values in (failures or {}).items()}
        self.calls: list[str] = []
        self.list_calls = 0
        self.first_text_latency_ms = first_text_latency_ms
        self.models = models or [
            ProviderModel(id=f"{name}/light-1:free", provider=self.name, is_free=True, tags=("lightweight",)),
            ProviderModel(id=f"{name}/code-1:free", provider=self.name, is_free=True, tags=("coding",)),
            ProviderModel(id=f"{name}/heavy-1:free", provider=self.name, is_free=True, tags=("heavyweight",)),
        ]
        default_classifications = []
        if len(self.models) >= 1:
            default_classifications.append({"id": self.models[0].id, "tags": ["lightweight"]})
        if len(self.models) >= 2:
            default_classifications.append({"id": self.models[1].id, "tags": ["coding"]})
        self.classification_payload = classification_payload or {"classifications": default_classifications}

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        self.list_calls += 1
        return list(self.models)

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        self.calls.append(backend_model)
        if payload.get("temperature") == 0 and "classifications" in str(self.classification_payload):
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


def test_models_endpoint_lists_aliases(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/v1/models")
        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload["data"]] == ["lightweight", "coding", "heavyweight"]


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
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/code-1:free"
        assert response.headers["x-ghostship-router-first-text-latency-ms"] == "12.5"


def test_chat_completion_fails_over_to_next_model(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "openrouter/heavy-1:free")),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/heavy-1:free"


def test_chat_completion_fails_over_across_providers_at_model_level(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["rate_limited"]})
    opencode = DummyProvider(
        "opencode-zen",
        models=[
            ProviderModel(id="qwen3-coder", provider="opencode-zen", is_free=False, tags=("coding",)),
            ProviderModel(id="gpt-5-nano", provider="opencode-zen", is_free=False, tags=("lightweight",)),
        ],
        first_text_latency_ms=8.0,
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "opencode/qwen3-coder")),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(
        config,
        providers={"openrouter": openrouter, "opencode-zen": opencode},
        state_store=SqliteStateStore(config.db_path),
    )
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-provider"] == "opencode-zen"
        assert response.headers["x-ghostship-router-backend-model"] == "qwen3-coder"


def test_model_missing_triggers_refresh(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter", failures={"openrouter/code-1:free": ["model_missing"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "openrouter/heavy-1:free")),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    before = provider.list_calls
    _, headers = service.chat_completions(ChatCompletionRequest.model_validate({"model": "coding", "messages": [{"role": "user", "content": "hello"}]}))
    assert provider.list_calls == before + 1
    assert headers["X-Ghostship-Router-Backend-Model"] == "openrouter/heavy-1:free"


def test_refresh_persists_inventory_across_service_restart(tmp_path: Path) -> None:
    openrouter = DummyProvider("openrouter")
    opencode = DummyProvider(
        "opencode-zen",
        models=[ProviderModel(id="qwen3-coder", provider="opencode-zen", is_free=False, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    store = SqliteStateStore(config.db_path)
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=store)
    service.refresh_inventory(reason="manual")
    restarted = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    preview = restarted.preview_routes("coding")
    assert any(candidate["backend_model"] == "openrouter/code-1:free" for candidate in preview)
    assert any(candidate["backend_model"] == "qwen3-coder" for candidate in preview)


def test_assisted_bucketing_uses_free_model(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(id="assistant-free:free", provider="openrouter", is_free=True, tags=()),
            ProviderModel(id="demo/light-1:free", provider="openrouter", is_free=True, tags=()),
            ProviderModel(id="demo/code-1:free", provider="openrouter", is_free=True, tags=()),
        ],
        classification_payload={
            "classifications": [
                {"id": "demo/light-1:free", "tags": ["lightweight"]},
                {"id": "demo/code-1:free", "tags": ["coding"]},
            ]
        },
    )
    config = make_config(
        tmp_path,
        assisted_bucket_model="assistant-free:free",
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    assert "assistant-free:free" in provider.calls
    preview = service.preview_routes("coding")
    assert any(candidate["backend_model"] == "demo/code-1:free" for candidate in preview)


def test_debug_endpoints_return_state_and_events(tmp_path: Path) -> None:
    provider = DummyProvider("openrouter")
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        state = client.get("/debug/state")
        events = client.get("/debug/events")
        assert state.status_code == 200
        assert events.status_code == 200
        assert state.json()["state"]["event_count"] >= 1
        assert state.json()["state"]["model_state"][0]["last_first_text_latency_ms"] == 12.5
        assert len(events.json()) >= 1


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
