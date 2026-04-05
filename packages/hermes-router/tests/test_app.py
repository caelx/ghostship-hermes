from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import NormalizedProviderError, ProviderChatResult, ProviderModel
from hermes_router.providers.gemini_fallback import GeminiFallbackAdapter
from hermes_router.service import RouterService
from hermes_router.state import SqliteStateStore


def make_config(tmp_path: Path, **overrides: Any) -> RouterConfig:
    state_dir = tmp_path / "state"
    base = RouterConfig(
        host="127.0.0.1",
        port=8788,
        log_level="info",
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
        gemini_fallback_model="google/gemini-fallback",
        assisted_bucket_model=None,
        assisted_bucket_batch_size=20,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free",)),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    return RouterConfig(**{**base.__dict__, **overrides})


class DummyProvider:
    name = "openrouter"

    def __init__(
        self,
        *,
        failures: dict[str, list[str]] | None = None,
        models: list[ProviderModel] | None = None,
        classification_payload: dict[str, Any] | None = None,
    ):
        self.failures = {key: list(values) for key, values in (failures or {}).items()}
        self.calls: list[str] = []
        self.list_calls = 0
        self.models = models or [
            ProviderModel(id="openrouter/light-1:free", provider=self.name, is_free=True, tags=("lightweight",)),
            ProviderModel(id="openrouter/code-1:free", provider=self.name, is_free=True, tags=("coding",)),
            ProviderModel(id="openrouter/heavy-1:free", provider=self.name, is_free=True, tags=("heavyweight",)),
        ]
        self.classification_payload = classification_payload or {
            "classifications": [
                {"id": "openrouter/light-1:free", "tags": ["lightweight"]},
                {"id": "openrouter/code-1:free", "tags": ["coding"]},
            ]
        }

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        self.list_calls += 1
        return list(self.models)

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        self.calls.append(backend_model)
        if backend_model.endswith(":free") and "classifications" in str(self.classification_payload) and payload.get("temperature") == 0:
            return ProviderChatResult(
                payload={
                    "id": "chatcmpl-classify",
                    "object": "chat.completion",
                    "model": backend_model,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": __import__("json").dumps(self.classification_payload)}, "finish_reason": "stop"}],
                },
                provider=self.name,
                backend_model=backend_model,
            )
        queued = self.failures.get(backend_model)
        if queued:
            failure = queued.pop(0)
            raise NormalizedProviderError(failure, failure, provider=self.name, backend_model=backend_model, retryable=(failure != "bad_request"))
        return ProviderChatResult(
            payload={
                "id": "chatcmpl-demo",
                "object": "chat.completion",
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            },
            provider=self.name,
            backend_model=backend_model,
        )


def test_models_endpoint_lists_aliases(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider()}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/v1/models")
        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload["data"]] == ["lightweight", "coding", "heavyweight"]


def test_readyz_is_unready_without_providers(tmp_path: Path) -> None:
    config = make_config(tmp_path, openrouter_api_key=None, opencode_api_key=None, gemini_fallback_model=None)
    service = RouterService(config, providers={}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ok"] is False


def test_chat_completion_routes_alias(tmp_path: Path) -> None:
    provider = DummyProvider()
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/code-1:free"


def test_chat_completion_fails_over_to_next_candidate(tmp_path: Path) -> None:
    provider = DummyProvider(failures={"openrouter/code-1:free": ["rate_limited"]})
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
        response = client.post(
            "/v1/chat/completions",
            json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-backend-model"] == "openrouter/heavy-1:free"


def test_chat_completion_uses_explicit_gemini_fallback(tmp_path: Path) -> None:
    provider = DummyProvider(failures={"openrouter/code-1:free": ["rate_limited"]})
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=("openrouter/light-1:free",)),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free",)),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=("openrouter/heavy-1:free",)),
        ),
    )
    service = RouterService(
        config,
        providers={
            "openrouter": provider,
            "gemini-fallback": GeminiFallbackAdapter(provider, model_id="google/gemini-fallback"),
        },
        state_store=SqliteStateStore(config.db_path),
    )
    with TestClient(create_app(config=config, service=service)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]},
        )
        assert response.status_code == 200
        assert response.headers["x-ghostship-router-fallback"] == "gemini"
        assert response.headers["x-ghostship-router-backend-provider"] == "gemini-fallback"


def test_model_missing_triggers_refresh(tmp_path: Path) -> None:
    provider = DummyProvider(failures={"openrouter/code-1:free": ["model_missing"]})
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
    payload, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
    )
    assert provider.list_calls == before + 1
    assert headers["X-Ghostship-Router-Backend-Model"] == "openrouter/heavy-1:free"


def test_refresh_persists_inventory_across_service_restart(tmp_path: Path) -> None:
    provider = DummyProvider()
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    store = SqliteStateStore(config.db_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=store)
    service.refresh_inventory(reason="manual")
    restarted = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    preview = restarted.preview_routes("coding")
    assert any(candidate["backend_model"] == "openrouter/code-1:free" for candidate in preview)


def test_assisted_bucketing_uses_free_model(tmp_path: Path) -> None:
    provider = DummyProvider(
        models=[
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
    provider = DummyProvider()
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    with TestClient(create_app(config=config, service=service)) as client:
        client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
        state = client.get("/debug/state")
        events = client.get("/debug/events")
        assert state.status_code == 200
        assert events.status_code == 200
        assert state.json()["state"]["event_count"] >= 1
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
