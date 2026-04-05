from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import NormalizedProviderError, ProviderChatResult, ProviderChatStreamEvent, ProviderModel
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
        alias_pin_overrides={"lightweight": (), "coding": (), "heavyweight": ()},
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
        default_rankings = []
        for model in self.models:
            default_rankings.append(
                {
                    "provider": model.provider,
                    "id": model.id,
                    "tags": list(model.tags),
                    "alias_scores": {
                        "lightweight": 10 if "lightweight" in model.tags else 1,
                        "coding": 10 if "coding" in model.tags else 1,
                        "heavyweight": 10 if "heavyweight" in model.tags else 1,
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
                f"{model.provider}::{model.id}"
                for model in self.models
                if alias in model.tags or alias.split("-", 1)[0] in model.id
            ] or [f"{model.provider}::{model.id}" for model in self.models]
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


def test_ranking_uses_healthy_free_lightweight_worker_and_persists_rankings(tmp_path: Path) -> None:
    provider = DummyProvider(
        "openrouter",
        models=[
            ProviderModel(id="assistant-free:free", provider="openrouter", is_free=True, tags=("lightweight",)),
            ProviderModel(id="demo/light-1:free", provider="openrouter", is_free=True, tags=()),
            ProviderModel(id="demo/code-1:free", provider="openrouter", is_free=True, tags=()),
        ],
        classification_payload={
            "models": [
                {
                    "provider": "openrouter",
                    "id": "demo/light-1:free",
                    "tags": ["lightweight"],
                    "alias_scores": {"lightweight": 11, "coding": 1, "heavyweight": 0},
                    "reason": "best lightweight model",
                    "confidence": 0.95,
                },
                {
                    "provider": "openrouter",
                    "id": "demo/code-1:free",
                    "tags": ["coding"],
                    "alias_scores": {"lightweight": 1, "coding": 11, "heavyweight": 0},
                    "reason": "best coding model",
                    "confidence": 0.94,
                },
            ]
        },
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    assert "assistant-free:free" in provider.calls
    state = service.debug_state()
    assert state["last_ranking_worker"]["backend_model"] == "assistant-free:free"
    assert state["state"]["ranking_count"] >= 2
    ranking = service.debug_rankings("coding")
    assert any(candidate["backend_model"] == "demo/code-1:free" and candidate["learned_ranking_score"] > 0 for candidate in ranking["candidates"])


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


def test_metrics_endpoint_exposes_request_failover_and_candidate_metrics(tmp_path: Path) -> None:
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
        models=[ProviderModel(id="qwen3-coder", provider="opencode-zen", is_free=False, tags=("coding",))],
    )
    config = make_config(
        tmp_path,
        provider_rate_limit_threshold=1.0,
        aliases=(
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=("openrouter/code-1:free", "opencode/qwen3-coder")),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": openrouter, "opencode-zen": opencode}, state_store=SqliteStateStore(config.db_path))
    _, headers = service.chat_completions(ChatCompletionRequest.model_validate({"model": "coding", "messages": [{"role": "user", "content": "hello"}]}))
    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    providers = service.debug_providers()
    openrouter_state = next(item for item in providers if item["provider_name"] == "openrouter")
    assert openrouter_state["cooldown_until"] > 0
    preview = service.preview_routes("coding")
    assert preview[0]["provider_name"] == "opencode-zen"


def test_overrides_survive_restart_and_affect_routing(tmp_path: Path) -> None:
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
    store.upsert_provider_override("openrouter", enabled=False)
    store.upsert_alias_pin("coding", ("opencode/qwen3-coder",))
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
            AliasConfig(name="lightweight", description="light", preferred_models=()),
            AliasConfig(name="coding", description="code", preferred_models=()),
            AliasConfig(name="heavyweight", description="heavy", preferred_models=()),
        ),
    )
    service = RouterService(config, providers={"openrouter": provider}, state_store=SqliteStateStore(config.db_path))
    service.refresh_inventory(reason="manual")
    preview = service.preview_routes("coding")
    assert preview
    assert preview[0]["backend_model"] == "openrouter/code-1:free"


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


def test_responses_stream_returns_openai_events_and_completed_payload(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    service = RouterService(config, providers={"openrouter": DummyProvider("openrouter")}, state_store=SqliteStateStore(config.db_path))
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
