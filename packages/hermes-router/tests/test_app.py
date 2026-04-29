from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, ProviderSeedPolicy, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import (
    NormalizedProviderError,
    ProviderChatResult,
    ProviderChatStreamEvent,
    ProviderChatStreamResult,
    ProviderChatStreamState,
    ProviderModel,
)
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
        alias_model_limit=3,
        allow_direct_models=False,
        allow_models=(),
        block_models=(),
        state_dir=state_dir,
        db_path=state_dir / "router.db",
        debug_event_limit=50,
        rolling_window_seconds=3600.0,
        provider_cooldown_seconds=300,
        provider_failure_threshold=3.0,
        provider_rate_limit_threshold=2.5,
        provider_timeout_threshold=2.5,
        provider_slow_first_text_threshold_ms=15000.0,
        provider_slow_total_threshold_ms=30000.0,
        provider_exhaustion_threshold=3.0,
        exhaustion_cooldown_ladder_seconds=(30, 60, 300, 600),
        provider_suspect_window_seconds=120,
        provider_disable_seconds=60,
        provider_probe_escalation_factor=2.0,
        provider_max_disable_seconds=600,
        provider_lane_limit=3,
        provider_throttle_ladder_seconds=(15, 30, 60),
        free_attempt_timeout_seconds=10.0,
        free_stream_first_byte_timeout_seconds=8.0,
        free_total_budget_seconds=24.0,
        fallback_timeout_seconds=45.0,
        primary_served_model="deepseek-v4-pro",
        fallback_served_model="minimax-m2.7",
        opencode_go_large_tool_history_primary_timeout_seconds=25.0,
        opencode_go_large_tool_history_fallback_timeout_seconds=75.0,
        trace_routing=False,
        openrouter_min_request_spacing_seconds=3.0,
        opencode_min_request_spacing_seconds=2.0,
        nvidia_build_min_request_spacing_seconds=1.0,
        openrouter_api_key=None,
        openrouter_base_url="https://openrouter.example/api/v1",
        openrouter_http_referer=None,
        openrouter_title=None,
        opencode_api_key=None,
        opencode_base_url="https://opencode.example/v1",
        opencode_go_api_key=None,
        opencode_go_base_url="https://opencode-go.example/v1",
        zenmux_api_key=None,
        zenmux_base_url="https://zenmux.example/v1",
        electron_hub_api_key=None,
        electron_hub_base_url="https://electron-hub.example/v1",
        nvidia_build_api_key=None,
        nvidia_build_base_url="https://integrate.api.nvidia.com/v1",
        disabled_providers=(),
        disabled_models=(),
        provider_weight_overrides={},
        model_weight_overrides={},
        alias_pin_overrides={"deepseek-v4-pro": (), "minimax-m2.7": ()},
        provider_priority=("nvidia-build", "opencode-zen", "zenmux", "electron-hub", "openrouter", "opencode-go"),
        provider_rpm_limits={
            "nvidia-build": 30,
            "opencode-zen": 30,
            "zenmux": 10,
            "electron-hub": 5,
            "openrouter": 20,
        },
        provider_seed_policies=(
            ProviderSeedPolicy(provider_name="nvidia-build", unused_models=("nvidia-bad",)),
            ProviderSeedPolicy(provider_name="opencode-zen"),
            ProviderSeedPolicy(provider_name="zenmux"),
            ProviderSeedPolicy(provider_name="electron-hub"),
            ProviderSeedPolicy(provider_name="openrouter"),
            ProviderSeedPolicy(provider_name="opencode-go"),
        ),
        aliases=(
            AliasConfig(
                name="deepseek-v4-pro",
                description="deepseek",
            ),
            AliasConfig(
                name="minimax-m2.7",
                description="minimax",
            ),
        ),
    )
    return RouterConfig(**{**base.__dict__, **overrides})


class FakeProvider:
    def __init__(
        self,
        name: str,
        *,
        models: list[ProviderModel],
        failures: dict[str, list[NormalizedProviderError]] | None = None,
    ) -> None:
        self.name = name
        self._models = list(models)
        self.failures = {key: list(value) for key, value in (failures or {}).items()}
        self.calls: list[str] = []
        self.timeouts: list[float | None] = []
        self.payloads: list[dict[str, Any]] = []
        self.responses: dict[str, list[dict[str, Any]]] = {}

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        del timeout
        return list(self._models)

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        self.timeouts.append(timeout)
        self.payloads.append(payload)
        self.calls.append(backend_model)
        failures = self.failures.get(backend_model) or []
        if failures:
            raise failures.pop(0)
        responses = self.responses.get(backend_model) or []
        if responses:
            response_payload = responses.pop(0)
        else:
            response_payload = {
                "id": f"chatcmpl-{backend_model}",
                "object": "chat.completion",
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": backend_model}, "finish_reason": "stop"}],
            }
        return ProviderChatResult(
            payload=response_payload,
            provider=self.name,
            backend_model=backend_model,
            first_text_latency_ms=12.0,
        )

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        result = self.chat_completions(backend_model, payload, timeout=timeout)
        state = ProviderChatStreamState(first_text_latency_ms=result.first_text_latency_ms, emitted_text=backend_model, final_payload=result.payload)
        return ProviderChatStreamResult(
            chunks=iter([ProviderChatStreamEvent(content=backend_model, finish_reason="stop")]),
            provider=self.name,
            backend_model=backend_model,
            state=state,
        )


class SlowProvider(FakeProvider):
    def __init__(self, name: str, *, models: list[ProviderModel], sleep_seconds: float) -> None:
        super().__init__(name, models=models)
        self.sleep_seconds = sleep_seconds
        self.started = threading.Event()

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        self.timeouts.append(timeout)
        self.payloads.append(payload)
        self.calls.append(backend_model)
        self.started.set()
        time.sleep(self.sleep_seconds)
        return ProviderChatResult(
            payload={
                "id": f"chatcmpl-{backend_model}",
                "object": "chat.completion",
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": backend_model}, "finish_reason": "stop"}],
            },
            provider=self.name,
            backend_model=backend_model,
            first_text_latency_ms=round(self.sleep_seconds * 1000, 2),
        )

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        self.timeouts.append(timeout)
        self.payloads.append(payload)
        self.calls.append(backend_model)
        state = ProviderChatStreamState()

        def chunks() -> Iterator[ProviderChatStreamEvent]:
            self.started.set()
            time.sleep(self.sleep_seconds)
            state.first_text_latency_ms = round(self.sleep_seconds * 1000, 2)
            state.emitted_text = backend_model
            yield ProviderChatStreamEvent(content=backend_model, finish_reason="stop")

        return ProviderChatStreamResult(chunks=chunks(), provider=self.name, backend_model=backend_model, state=state)


def free_model(model_id: str, provider: str, *, tags: tuple[str, ...] = ("agentic",), modalities: tuple[str, ...] = ("text",)) -> ProviderModel:
    return ProviderModel(
        id=model_id,
        provider=provider,
        is_free=True,
        tags=tags,
        metadata={"supported_parameters": ["tools", "tool_choice"], "input_modalities": ["text"], "output_modalities": list(modalities)},
    )


def paid_model(model_id: str, provider: str, *, tags: tuple[str, ...] = ("agentic",), modalities: tuple[str, ...] = ("text",)) -> ProviderModel:
    return ProviderModel(
        id=model_id,
        provider=provider,
        is_free=False,
        tags=tags,
        metadata={"supported_parameters": ["tools", "tool_choice"], "input_modalities": ["text"], "output_modalities": list(modalities)},
    )


def paid_messages_tool_model(model_id: str, provider: str, *, tags: tuple[str, ...] = ("agentic",)) -> ProviderModel:
    return ProviderModel(
        id=model_id,
        provider=provider,
        is_free=False,
        tags=tags,
        metadata={
            "endpoint_family": "messages",
            "provider_metadata": {"tool_call": True},
            "input_modalities": ["text"],
            "output_modalities": ["text"],
        },
    )


def paid_nested_multimodal_model(model_id: str, provider: str) -> ProviderModel:
    return ProviderModel(
        id=model_id,
        provider=provider,
        is_free=False,
        tags=("agentic",),
        metadata={
            "provider_metadata": {
                "modalities": {
                    "input": ["text", "image", "video"],
                    "output": ["text"],
                },
                "tool_call": True,
            },
        },
    )


def simple_chat_payload(model: str) -> dict[str, Any]:
    return {"model": model, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 16}


def large_tool_history_payload(model: str) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    for index in range(11):
        call_id = f"call_{index}"
        messages.extend(
            [
                {"role": "user", "content": f"step {index}"},
                {
                    "role": "assistant",
                    "content": None,
                    "reasoning_content": "thinking",
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": "skill_view", "arguments": "{\"name\":\"health\"}"},
                        }
                    ],
                },
                {"role": "tool", "tool_call_id": call_id, "content": "ok"},
            ]
        )
    messages.append({"role": "user", "content": "continue"})
    return {
        "model": model,
        "stream": True,
        "messages": messages,
        "tools": [{"type": "function", "function": {"name": "skill_view", "parameters": {"type": "object"}}}],
        "tool_choice": "auto",
    }


def make_service(tmp_path: Path, *, providers: dict[str, FakeProvider], config: RouterConfig | None = None) -> RouterService:
    resolved = config or make_config(tmp_path)
    store = SqliteStateStore(resolved.db_path)
    service = RouterService(resolved, providers=providers, state_store=store)
    service.refresh_inventory(reason="test")
    return service


def test_config_default_rpms_include_zenmux_and_electron_hub(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path / "state"))
    config = RouterConfig.from_env()

    assert config.provider_rpm_limits["zenmux"] == 10
    assert config.provider_rpm_limits["electron-hub"] == 5
    assert config.provider_rpm_limits["openrouter"] == 20
    assert config.provider_rpm_limits["nvidia-build"] == 30
    assert config.provider_rpm_limits["opencode-zen"] == 30
    assert config.free_attempt_timeout_seconds == 10.0
    assert config.free_stream_first_byte_timeout_seconds == 8.0
    assert config.free_total_budget_seconds == 24.0
    assert config.fallback_timeout_seconds == 45.0
    assert config.primary_served_model == "deepseek-v4-pro"
    assert config.fallback_served_model == "minimax-m2.7"
    assert config.opencode_go_large_tool_history_primary_timeout_seconds == 25.0
    assert config.opencode_go_large_tool_history_fallback_timeout_seconds == 75.0


def test_config_provider_rpms_are_overrideable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("GHOSTSHIP_ROUTER_PROVIDER_RPM_ZENMUX", "12")
    monkeypatch.setenv("GHOSTSHIP_ROUTER_PROVIDER_RPM_ELECTRON_HUB", "7")
    config = RouterConfig.from_env()

    assert config.provider_rpm_limits["zenmux"] == 12
    assert config.provider_rpm_limits["electron-hub"] == 7


def test_zenmux_and_electron_hub_register_when_keys_are_configured(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        zenmux_api_key="zenmux-key",
        electron_hub_api_key="electron-key",
    )
    service = RouterService(config)

    assert isinstance(service.providers["zenmux"], OpencodeZenProvider)
    assert isinstance(service.providers["electron-hub"], OpencodeZenProvider)
    assert service.providers["zenmux"].name == "zenmux"
    assert service.providers["electron-hub"].name == "electron-hub"


def test_models_endpoint_exposes_only_opencode_go_ids_with_free_equivalents(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        aliases=(
            *make_config(tmp_path).aliases,
            AliasConfig(name="unmatched-go-model", description="hidden", preferred_models=("opencode-go/unmatched-go-model",)),
        ),
    )
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen"), free_model("minimax-m2.7", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go"), paid_model("minimax-m2.7", "opencode-go"), paid_model("unmatched-go-model", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["data"]] == ["deepseek-v4-pro", "minimax-m2.7"]
    deepseek = payload["data"][0]["metadata"]
    assert deepseek["free_provider_count"] == 2
    assert deepseek["free_providers"] == ["nvidia-build", "opencode-zen"]
    assert deepseek["free_provider_state"]["nvidia-build"]["rpm_limit"] == 30


def test_deepseek_routes_free_equivalents_before_opencode_go_fallback(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )

    preview = service.preview_routes("deepseek-v4-pro")

    assert [(item["provider_name"], item["backend_model"]) for item in preview] == [
        ("nvidia-build", "deepseek-ai/deepseek-v4-pro"),
        ("opencode-zen", "deepseek-v4-pro"),
        ("opencode-go", "deepseek-v4-pro"),
    ]
    assert preview[-1]["is_free"] is False
    assert preview[-1]["is_fallback"] is True


def test_seeded_zenmux_and_electron_hub_are_free_candidates(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "zenmux": FakeProvider("zenmux", models=[free_model("deepseek/deepseek-v4-pro-free", "zenmux")]),
            "electron-hub": FakeProvider("electron-hub", models=[free_model("deepseek-v4-pro:free", "electron-hub")]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )

    preview = service.preview_routes("deepseek-v4-pro")

    assert [(item["provider_name"], item["backend_model"]) for item in preview] == [
        ("zenmux", "deepseek/deepseek-v4-pro-free"),
        ("electron-hub", "deepseek-v4-pro:free"),
        ("opencode-go", "deepseek-v4-pro"),
    ]
    assert preview[0]["is_free"] is True
    assert preview[1]["is_free"] is True


def test_missing_dynamic_equivalence_is_not_exposed(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )

    preview = service.preview_routes("deepseek-v4-pro")

    assert preview == []


def test_default_router_config_does_not_hardcode_provider_backend_models(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GHOSTSHIP_ROUTER_STATE_DIR", str(tmp_path))
    config = RouterConfig.from_env()

    aliases = {alias.name: alias.preferred_models for alias in config.aliases}
    seed_map = config.provider_seed_map()

    assert aliases["deepseek-v4-pro"] == ()
    assert aliases["minimax-m2.7"] == ()
    assert all(policy.seeded_models == () for policy in seed_map.values())


def test_round_robin_distributes_across_eligible_free_equivalents(tmp_path: Path) -> None:
    providers = {
        "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
        "opencode-zen": FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")]),
        "zenmux": FakeProvider("zenmux", models=[free_model("deepseek/deepseek-v4-pro-free", "zenmux")]),
        "electron-hub": FakeProvider("electron-hub", models=[free_model("deepseek-v4-pro:free", "electron-hub")]),
        "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
    }
    service = make_service(tmp_path, providers=providers)

    used: list[str] = []
    for _ in range(4):
        _, headers = service.chat_completions(
            ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
        )
        used.append(headers["X-Ghostship-Router-Backend-Provider"])

    assert used == ["nvidia-build", "opencode-zen", "nvidia-build", "opencode-zen"]
    assert providers["opencode-go"].calls == []


def test_rpm_exhaustion_skips_free_provider_until_window_clears(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        provider_rpm_limits={"electron-hub": 1},
        provider_priority=("electron-hub", "opencode-go"),
        aliases=(
            AliasConfig(
                name="deepseek-v4-pro",
                description="deepseek",
                preferred_models=("electron-hub/deepseek-v4-pro:free", "opencode-go/deepseek-v4-pro"),
            ),
        ),
    )
    electron = FakeProvider("electron-hub", models=[free_model("deepseek-v4-pro:free", "electron-hub")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, config=config, providers={"electron-hub": electron, "opencode-go": go})

    _, first_headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )
    _, second_headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello again"}]})
    )

    assert first_headers["X-Ghostship-Router-Backend-Provider"] == "electron-hub"
    assert second_headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert electron.calls == ["deepseek-v4-pro:free"]
    assert go.calls == ["deepseek-v4-pro"]


def test_quota_exhaustion_falls_back_to_same_model_opencode_go(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "quota_exhausted",
                    "quota done",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=False,
                    details={"hard_exhaustion": True},
                )
            ]
        },
    )
    zen = FakeProvider(
        "opencode-zen",
        models=[free_model("deepseek-v4-pro", "opencode-zen")],
        failures={
            "deepseek-v4-pro": [
                NormalizedProviderError(
                    "rate_limited",
                    "rate limited",
                    provider="opencode-zen",
                    backend_model="deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": nvidia,
            "opencode-zen": zen,
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": go,
        },
    )

    payload, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert payload["choices"][0]["message"]["content"] == "deepseek-v4-pro"
    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert nvidia.calls == ["deepseek-ai/deepseek-v4-pro"]
    assert zen.calls == ["deepseek-v4-pro"]
    assert go.calls == ["deepseek-v4-pro"]


def test_timeout_failure_tries_another_free_provider_before_opencode_go(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    assert nvidia.calls == ["deepseek-ai/deepseek-v4-pro"]
    assert zen.calls == ["deepseek-v4-pro"]
    assert go.calls == []


def test_stream_timeout_failure_tries_another_free_provider_before_opencode_go(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})

    plan = service.stream_chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "stream": True, "messages": [{"role": "user", "content": "hello"}]})
    )
    body = "".join(plan.body)

    assert plan.headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    assert "deepseek-v4-pro" in body
    assert nvidia.calls == ["deepseek-ai/deepseek-v4-pro"]
    assert zen.calls == ["deepseek-v4-pro"]
    assert go.calls == []


def test_free_provider_attempts_use_aggressive_timeouts_before_fallback(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert nvidia.timeouts == [10.0]
    assert go.timeouts == [45.0]
    event = service.state_store.get_route_events(limit=10, provider_name="nvidia-build", success=False)[0]
    assert event["category"] == "request_timeout"
    assert event["details"]["request_shape"]["shape_key"] == "text"
    assert event["details"]["route"]["attempt_timeout_seconds"] == 10.0


def test_free_provider_wall_clock_deadline_skips_slow_non_stream_call(tmp_path: Path) -> None:
    slow = SlowProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        sleep_seconds=2.0,
    )
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(
        tmp_path,
        config=make_config(tmp_path, free_attempt_timeout_seconds=0.1),
        providers={"nvidia-build": slow, "opencode-zen": zen, "opencode-go": go},
    )

    started_at = time.monotonic()
    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert time.monotonic() - started_at < 1.0
    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    assert slow.calls == ["deepseek-ai/deepseek-v4-pro"]
    assert zen.calls == ["deepseek-v4-pro"]
    event = service.state_store.get_route_events(limit=10, provider_name="nvidia-build", success=False)[0]
    assert event["category"] == "request_timeout"
    assert event["details"]["provider_error"]["deadline_enforced"] is True


def test_free_provider_wall_clock_deadline_skips_slow_stream_first_byte(tmp_path: Path) -> None:
    slow = SlowProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        sleep_seconds=2.0,
    )
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(
        tmp_path,
        config=make_config(tmp_path, free_stream_first_byte_timeout_seconds=0.1),
        providers={"nvidia-build": slow, "opencode-zen": zen, "opencode-go": go},
    )

    started_at = time.monotonic()
    plan = service.stream_chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "stream": True, "messages": [{"role": "user", "content": "hello"}]})
    )
    body = "".join(plan.body)

    assert time.monotonic() - started_at < 1.0
    assert plan.headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    assert "deepseek-v4-pro" in body
    event = service.state_store.get_route_events(limit=10, provider_name="nvidia-build", success=False)[0]
    assert event["category"] == "first_byte_timeout"
    assert event["details"]["provider_error"]["deadline_enforced"] is True


def test_all_route_timeouts_return_nonretryable_failed_dependency(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    go = FakeProvider(
        "opencode-go",
        models=[paid_model("deepseek-v4-pro", "opencode-go")],
        failures={
            "deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="opencode-go",
                    backend_model="deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post(
        "/v1/chat/completions",
        json={"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 424
    assert "All route candidates failed" in response.json()["error"]["message"]


def test_post_attempt_exhaustion_records_skipped_suppressed_fallback(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})
    service.state_store.record_shape_result(
        "opencode-go",
        "deepseek-v4-pro",
        "stream+tools+tool_history+reasoning|size=large",
        success=False,
        category="request_timeout",
        latency_ms=25000.0,
        first_text_latency_ms=None,
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post("/v1/chat/completions", json=large_tool_history_payload("deepseek-v4-pro"))

    assert response.status_code == 424
    assert nvidia.calls == ["deepseek-ai/deepseek-v4-pro"]
    assert go.calls == []
    exhausted = service.state_store.get_route_events(limit=1, provider_name="router", category="route_exhausted")[0]
    assert exhausted["retryable"] is False
    assert exhausted["details"]["message"] == "All route candidates failed for alias 'deepseek-v4-pro'."
    assert exhausted["details"]["route"]["shape_key"] == "stream+tools+tool_history+reasoning"
    assert exhausted["details"]["route"]["size_bucket"] == "large"
    assert exhausted["details"]["attempted"] == [
        {"provider_name": "nvidia-build", "backend_model": "deepseek-ai/deepseek-v4-pro"}
    ]
    assert exhausted["details"]["attempt_errors"][0]["provider"] == "nvidia-build"
    assert exhausted["details"]["attempt_errors"][0]["category"] == "request_timeout"
    assert exhausted["details"]["skipped"] == [
        {
            "provider_name": "opencode-go",
            "backend_model": "deepseek-v4-pro",
            "is_free": False,
            "reason": "shape_suppressed",
        }
    ]


def test_large_tool_history_deepseek_opencode_go_timeout_fast_fails_next_attempt(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    go = FakeProvider(
        "opencode-go",
        models=[paid_model("deepseek-v4-pro", "opencode-go")],
        failures={
            "deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="opencode-go",
                    backend_model="deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})
    client = TestClient(create_app(service=service, config=service.config))

    first = client.post("/v1/chat/completions", json=large_tool_history_payload("deepseek-v4-pro"))
    second = client.post("/v1/chat/completions", json=large_tool_history_payload("deepseek-v4-pro"))
    routes = service.debug_routes("deepseek-v4-pro", shape_key="stream+tools+tool_history+reasoning", size_bucket="large")

    assert first.status_code == 424
    assert second.status_code == 424
    assert nvidia.timeouts == [10.0]
    assert go.timeouts == [25.0]
    skipped = {(item["provider_name"], item["backend_model"]): item["reason"] for item in routes["skipped"]}
    assert skipped[("opencode-go", "deepseek-v4-pro")] == "shape_suppressed"
    exhausted = service.state_store.get_route_events(limit=1, provider_name="router", category="route_exhausted")[0]
    assert exhausted["retryable"] is False
    assert exhausted["details"]["route"]["shape_key"] == "stream+tools+tool_history+reasoning"
    assert exhausted["details"]["route"]["size_bucket"] == "large"
    assert exhausted["details"]["skipped"] == [
        {
            "provider_name": "nvidia-build",
            "backend_model": "deepseek-ai/deepseek-v4-pro",
            "is_free": True,
            "reason": "shape_suppressed",
        },
        {
            "provider_name": "opencode-go",
            "backend_model": "deepseek-v4-pro",
            "is_free": False,
            "reason": "shape_suppressed",
        },
    ]


def test_large_tool_history_minimax_fallback_timeout_survives_deepseek_suppression(tmp_path: Path) -> None:
    config = make_config(tmp_path, free_total_budget_seconds=0.0)
    zenmux = FakeProvider("zenmux", models=[free_model("minimax/minimax-m2.7", "zenmux")])
    go = FakeProvider(
        "opencode-go",
        models=[
            paid_model("deepseek-v4-pro", "opencode-go"),
            paid_model("minimax-m2.7", "opencode-go"),
        ],
    )
    service = make_service(tmp_path, config=config, providers={"zenmux": zenmux, "opencode-go": go})
    service.state_store.record_shape_result(
        "opencode-go",
        "deepseek-v4-pro",
        "stream+tools+tool_history+reasoning|size=large",
        success=False,
        category="request_timeout",
        latency_ms=25000.0,
        first_text_latency_ms=None,
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post("/v1/chat/completions", json=large_tool_history_payload("minimax-m2.7"))
    routes = service.debug_routes("minimax-m2.7", shape_key="stream+tools+tool_history+reasoning", size_bucket="large")

    assert response.status_code == 200
    assert response.headers["x-ghostship-router-backend-provider"] == "opencode-go"
    assert go.timeouts == [75.0]
    assert ("opencode-go", "minimax-m2.7") in {
        (candidate["provider_name"], candidate["backend_model"]) for candidate in routes["candidates"]
    }


def test_hermes_style_fallback_after_primary_424_does_not_retry_primary(tmp_path: Path) -> None:
    config = make_config(tmp_path, free_total_budget_seconds=0.0)
    go = FakeProvider(
        "opencode-go",
        models=[
            paid_model("deepseek-v4-pro", "opencode-go"),
            paid_model("minimax-m2.7", "opencode-go"),
        ],
        failures={
            "deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="opencode-go",
                    backend_model="deepseek-v4-pro",
                    retryable=True,
                )
            ]
        },
    )
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "zenmux": FakeProvider("zenmux", models=[free_model("minimax/minimax-m2.7", "zenmux")]),
            "opencode-go": go,
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    primary = client.post("/v1/chat/completions", json=large_tool_history_payload("deepseek-v4-pro"))
    fallback = client.post("/v1/chat/completions", json=large_tool_history_payload("minimax-m2.7"))

    assert primary.status_code == 424
    assert fallback.status_code == 200
    assert go.calls == ["deepseek-v4-pro", "minimax-m2.7"]


def test_shape_timeout_suppression_does_not_poison_text_shape(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "stream+tools",
        success=False,
        category="first_byte_timeout",
        latency_ms=8000.0,
        first_text_latency_ms=None,
    )

    stream_tool_routes = service.debug_routes("deepseek-v4-pro", shape_key="stream+tools")
    text_routes = service.debug_routes("deepseek-v4-pro", shape_key="text")

    assert stream_tool_routes["skipped"][0]["provider_name"] == "nvidia-build"
    assert stream_tool_routes["skipped"][0]["reason"] == "shape_suppressed"
    assert text_routes["candidates"][0]["provider_name"] == "nvidia-build"


def test_slow_shape_health_reduces_weight_without_removing_provider(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "text",
        success=True,
        category="slow_success",
        latency_ms=40000.0,
        first_text_latency_ms=20000.0,
        slow_success=True,
    )

    routes = service.preview_routes("deepseek-v4-pro")
    nvidia_route = next(item for item in routes if item["provider_name"] == "nvidia-build")
    zen_route = next(item for item in routes if item["provider_name"] == "opencode-zen")

    assert nvidia_route["health_score"] < zen_route["health_score"]
    assert nvidia_route["effective_weight"] < zen_route["effective_weight"]
    assert "nvidia-build" in [item["provider_name"] for item in routes]


def test_free_budget_exhaustion_records_skip_and_uses_opencode_go(tmp_path: Path) -> None:
    config = make_config(tmp_path, free_total_budget_seconds=0.0)
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, config=config, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert nvidia.calls == []
    assert zen.calls == []
    assert go.calls == ["deepseek-v4-pro"]
    skipped = service.state_store.get_route_events(limit=10, category="request_budget_exhausted", success=False)
    assert {event["provider_name"] for event in skipped} == {"nvidia-build", "opencode-zen"}


def test_shape_probe_success_lowers_suppression_level(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "stream",
        success=False,
        category="first_byte_timeout",
        latency_ms=8000.0,
        first_text_latency_ms=None,
    )
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "stream",
        success=True,
        category=None,
        latency_ms=1200.0,
        first_text_latency_ms=900.0,
    )
    health_after_one = service.state_store.get_shape_health()["nvidia-build::deepseek-ai/deepseek-v4-pro::stream"]
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "stream",
        success=True,
        category=None,
        latency_ms=1100.0,
        first_text_latency_ms=800.0,
    )
    health_after_two = service.state_store.get_shape_health()["nvidia-build::deepseek-ai/deepseek-v4-pro::stream"]

    assert health_after_one["suppression_level"] == 1
    assert health_after_two["suppression_level"] == 0


def test_timeout_score_suppresses_only_unhealthy_free_candidate(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})
    now = time.time()
    with sqlite3.connect(service.config.db_path) as connection:
        connection.execute(
            """
            INSERT INTO model_state (provider_name, backend_model, recent_timeout, updated_at)
            VALUES ('nvidia-build', 'deepseek-ai/deepseek-v4-pro', 3.0, ?)
            ON CONFLICT(provider_name, backend_model) DO UPDATE SET
              recent_timeout = 3.0,
              cooldown_until = 0,
              updated_at = excluded.updated_at
            """,
            (now,),
        )
    service.state_store._invalidate_read_caches("_model_state_cache")

    service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "skip slow free provider"}]})
    )

    assert nvidia.calls == []
    assert zen.calls == ["deepseek-v4-pro"]
    assert go.calls == []
    candidates = service.preview_routes("deepseek-v4-pro")
    assert [candidate["provider_name"] for candidate in candidates] == ["opencode-zen", "opencode-go"]
    route_debug = service.debug_routes("deepseek-v4-pro")
    assert route_debug["skipped"][0]["provider_name"] == "nvidia-build"
    assert route_debug["skipped"][0]["reason"] == "model_timeout_guard"
    assert route_debug["skipped"][0]["state"]["timeout_guard_until"] is not None


def test_opencode_go_timeout_cooldown_does_not_hide_other_fallback_models(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "zenmux": FakeProvider("zenmux", models=[free_model("minimax/minimax-m2.7", "zenmux")]),
            "opencode-go": FakeProvider(
                "opencode-go",
                models=[
                    paid_model("deepseek-v4-pro", "opencode-go"),
                    paid_model("minimax-m2.7", "opencode-go"),
                ],
            ),
        },
    )
    service.state_store.set_provider_cooldown(
        "opencode-go",
        cooldown_until=time.time() + 300,
        category="timeout",
        details={"source": "test"},
    )
    service.state_store.apply_failure(
        "opencode-go",
        "deepseek-v4-pro",
        category="request_timeout",
        retryable=True,
        cooldown_model=False,
    )

    routes = service.debug_routes("minimax-m2.7", shape_key="stream+tools+tool_history+reasoning")
    candidates = [(candidate["provider_name"], candidate["backend_model"]) for candidate in routes["candidates"]]

    assert ("opencode-go", "minimax-m2.7") in candidates
    assert not any(
        skipped["provider_name"] == "opencode-go" and skipped["reason"] == "provider_cooldown"
        for skipped in routes["skipped"]
    )


def test_slow_latency_score_suppresses_unhealthy_free_candidate(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})
    now = time.time()
    with sqlite3.connect(service.config.db_path) as connection:
        connection.execute(
            """
            INSERT INTO model_state (provider_name, backend_model, first_text_latency_avg_ms, updated_at)
            VALUES ('nvidia-build', 'deepseek-ai/deepseek-v4-pro', 45000.0, ?)
            ON CONFLICT(provider_name, backend_model) DO UPDATE SET
              first_text_latency_avg_ms = 45000.0,
              cooldown_until = 0,
              updated_at = excluded.updated_at
            """,
            (now,),
        )
    service.state_store._invalidate_read_caches("_model_state_cache")

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "skip slow free provider"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"
    assert nvidia.calls == []
    assert zen.calls == ["deepseek-v4-pro"]
    assert go.calls == []
    route_debug = service.debug_routes("deepseek-v4-pro")
    assert route_debug["skipped"][0]["provider_name"] == "nvidia-build"
    assert route_debug["skipped"][0]["reason"] == "model_slow_first_text_guard"
    assert route_debug["skipped"][0]["state"]["slow_guard_until"] is not None


def test_slow_free_provider_falls_back_to_opencode_go_when_no_other_free_is_eligible(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})
    now = time.time()
    with sqlite3.connect(service.config.db_path) as connection:
        connection.execute(
            """
            INSERT INTO provider_state (provider_name, first_text_latency_avg_ms, updated_at)
            VALUES ('nvidia-build', 45000.0, ?)
            ON CONFLICT(provider_name) DO UPDATE SET
              first_text_latency_avg_ms = 45000.0,
              cooldown_until = 0,
              updated_at = excluded.updated_at
            """,
            (now,),
        )
    service.state_store._invalidate_read_caches("_provider_state_cache")

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "fallback after slow free provider"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert nvidia.calls == []
    assert go.calls == ["deepseek-v4-pro"]


def test_paid_free_provider_backend_is_not_used_as_free_equivalent(tmp_path: Path) -> None:
    zenmux = FakeProvider(
        "zenmux",
        models=[
            paid_model("deepseek/deepseek-v4-pro", "zenmux"),
            free_model("deepseek/deepseek-v4-pro-free", "zenmux"),
        ],
    )
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"zenmux": zenmux, "opencode-go": go})

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "zenmux"
    assert zenmux.calls == ["deepseek/deepseek-v4-pro-free"]
    assert go.calls == []

    service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello again"}]})
    )

    assert zenmux.calls == ["deepseek/deepseek-v4-pro-free", "deepseek/deepseek-v4-pro-free"]


def test_opencode_go_fallback_is_not_removed_by_provider_pacing(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        provider_priority=("nvidia-build", "opencode-go"),
        provider_rpm_limits={"nvidia-build": 30},
    )
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, config=config, providers={"nvidia-build": nvidia, "opencode-go": go})
    now = time.time()
    with sqlite3.connect(service.config.db_path) as connection:
        connection.execute(
            """
            INSERT INTO provider_state (provider_name, cooldown_until, updated_at)
            VALUES ('nvidia-build', ?, ?)
            ON CONFLICT(provider_name) DO UPDATE SET cooldown_until = excluded.cooldown_until, updated_at = excluded.updated_at
            """,
            (now + 300, now),
        )
        connection.execute(
            """
            INSERT INTO provider_state (provider_name, next_request_at, updated_at)
            VALUES ('opencode-go', ?, ?)
            ON CONFLICT(provider_name) DO UPDATE SET next_request_at = excluded.next_request_at, updated_at = excluded.updated_at
            """,
            (now + 300, now),
        )
    service.state_store._invalidate_read_caches("_provider_state_cache")

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert nvidia.calls == []
    assert go.calls == ["deepseek-v4-pro"]


def test_opencode_go_is_paid_fallback_not_free_provider(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[]),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("minimax-m2.7", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("minimax-m2.7", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    payload = client.get("/v1/models").json()
    minimax = next(item for item in payload["data"] if item["id"] == "minimax-m2.7")

    assert minimax["metadata"]["free_provider_count"] == 1
    assert minimax["metadata"]["free_providers"] == ["opencode-zen"]
    assert minimax["metadata"]["candidates"][-1]["provider_name"] == "opencode-go"
    assert minimax["metadata"]["candidates"][-1]["is_free"] is False


def test_retired_aliases_are_rejected(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    coding = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})
    agentic = client.post("/v1/chat/completions", json={"model": "agentic", "messages": [{"role": "user", "content": "hello"}]})

    assert coding.status_code == 404
    assert agentic.status_code == 404
    assert "retired" in coding.json()["error"]["message"]
    assert "retired" in agentic.json()["error"]["message"]


def test_debug_summary_reports_provider_state_and_candidate_order(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="secret")
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.get("/debug/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["router"]["auth_required"] is True
    assert payload["router"]["provider_priority"] == ["nvidia-build", "opencode-zen", "openrouter", "opencode-go"]
    assert "rolling_route_stats" in payload["router"]
    assert payload["providers"][0]["rpm"]["rpm_limit"] == 30
    assert payload["aliases"]["deepseek-v4-pro"]["selected_provider"] == "nvidia-build"


def test_debug_health_reports_shape_health(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    service.state_store.record_shape_result(
        "nvidia-build",
        "deepseek-ai/deepseek-v4-pro",
        "stream+tools",
        success=False,
        category="first_byte_timeout",
        latency_ms=8000.0,
        first_text_latency_ms=None,
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.get("/debug/health")

    assert response.status_code == 200
    shape = response.json()["shapes"][0]
    assert shape["provider_name"] == "nvidia-build"
    assert shape["shape_key"] == "stream+tools"
    assert shape["size_bucket"] == "any"
    assert shape["suppression_active"] is True
    assert shape["health_score"] < 1.0


def test_readyz_stays_responsive_during_slow_chat_request(tmp_path: Path) -> None:
    slow = SlowProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        sleep_seconds=1.5,
    )
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": slow,
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))
    result: dict[str, Any] = {}

    def post_chat() -> None:
        result["response"] = client.post(
            "/v1/chat/completions",
            json={"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]},
        )

    thread = threading.Thread(target=post_chat)
    thread.start()
    assert slow.started.wait(timeout=2)

    started_at = time.monotonic()
    ready_response = client.get("/readyz")
    ready_elapsed = time.monotonic() - started_at

    thread.join(timeout=5)
    assert not thread.is_alive()
    assert ready_response.status_code == 200
    assert ready_elapsed < 0.5
    assert result["response"].status_code == 200


def test_debug_route_events_filters_and_reports_request_shape(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")],
        failures={
            "deepseek-ai/deepseek-v4-pro": [
                NormalizedProviderError(
                    "timeout",
                    "request timed out",
                    provider="nvidia-build",
                    backend_model="deepseek-ai/deepseek-v4-pro",
                    retryable=True,
                    details={"method": "POST", "path": "/chat/completions", "timeout": 30.0},
                )
            ]
        },
    )
    zen = FakeProvider("opencode-zen", models=[free_model("deepseek-v4-pro", "opencode-zen")])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-zen": zen, "opencode-go": go})
    client = TestClient(create_app(service=service, config=service.config))

    chat_response = client.post(
        "/v1/chat/completions",
        json={
            "model": "deepseek-v4-pro",
            "messages": [{"role": "user", "content": "call the tool"}],
            "tools": [{"type": "function", "function": {"name": "ping", "parameters": {"type": "object"}}}],
            "stream_options": {"include_usage": True},
        },
    )
    route_response = client.get("/debug/route-events", params={"provider_name": "nvidia-build", "category": "request_timeout", "success": False})

    assert chat_response.status_code == 200
    assert route_response.status_code == 200
    payload = route_response.json()
    assert payload["filters"]["provider_name"] == "nvidia-build"
    assert payload["filters"]["category"] == "request_timeout"
    assert payload["filters"]["success"] is False
    assert len(payload["events"]) == 1
    event = payload["events"][0]
    assert isinstance(event["id"], int)
    assert event["provider_name"] == "nvidia-build"
    assert event["backend_model"] == "deepseek-ai/deepseek-v4-pro"
    request_shape = event["details"]["request_shape"]
    assert request_shape["model"] == "deepseek-v4-pro"
    assert request_shape["shape_key"] == "tools"
    assert request_shape["size_bucket"] == "small"
    assert request_shape["prompt_token_estimate"] > 0
    assert request_shape["message_count"] == 1
    assert request_shape["role_counts"] == {"user": 1}
    assert request_shape["has_tools"] is True
    assert request_shape["tool_count"] == 1
    assert request_shape["has_stream_options"] is True


def test_request_debug_shape_counts_hermes_tool_history() -> None:
    shape = RouterService._request_debug_shape(
        {
            "model": "deepseek-v4-pro",
            "messages": [
                {
                    "role": "assistant",
                    "content": None,
                    "reasoning_content": "thinking",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "skill_view", "arguments": "{\"name\":\"health\"}"},
                        }
                    ],
                },
                {"role": "tool", "tool_call_id": "call_1", "content": "ok"},
                {"role": "user", "content": "continue"},
            ],
            "tools": [{"type": "function", "function": {"name": "skill_view", "parameters": {"type": "object"}}}],
            "tool_choice": "auto",
            "max_tokens": 64,
        }
    )

    assert shape["message_count"] == 3
    assert shape["size_bucket"] == "small"
    assert shape["prompt_token_estimate"] > 0
    assert shape["role_counts"] == {"assistant": 1, "tool": 1, "user": 1}
    assert shape["assistant_tool_call_messages"] == 1
    assert shape["assistant_reasoning_messages"] == 1
    assert shape["tool_result_messages"] == 1
    assert shape["null_content_messages"] == 1
    assert shape["tool_choice"] == "auto"
    assert shape["has_max_tokens"] is True


def test_configured_api_key_requires_authorization(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="secret")
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    unauthorized = client.get("/v1/models")
    authorized = client.get("/v1/models", headers={"Authorization": "Bearer secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_chat_message_preserves_assistant_tool_calls_and_null_content() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "model": "deepseek-v4-pro",
            "messages": [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "skill_view", "arguments": "{\"name\":\"ghostship-media-services-health\"}"},
                        }
                    ],
                    "reasoning_content": "selected the tool",
                },
                {"role": "tool", "tool_call_id": "call_1", "content": "ok"},
                {"role": "user", "content": "summarize"},
            ],
            "tools": [{"type": "function", "function": {"name": "skill_view", "parameters": {"type": "object"}}}],
        }
    )

    payload = RouterService._chat_request_payload(RouterService.__new__(RouterService), request)

    assert payload["messages"][0]["content"] is None
    assert payload["messages"][0]["tool_calls"][0]["id"] == "call_1"
    assert payload["messages"][0]["reasoning_content"] == "selected the tool"
    assert payload["messages"][1]["tool_call_id"] == "call_1"


def test_orphan_tool_message_is_rejected_before_routing(tmp_path: Path) -> None:
    provider = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")]),
            "opencode-go": provider,
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "tool", "tool_call_id": "missing", "content": "ok"},
                {"role": "user", "content": "continue"},
            ],
        },
    )

    assert response.status_code == 400
    assert "unknown tool_call_id" in response.json()["error"]["message"]
    assert provider.calls == []


def test_messages_family_tool_call_models_remain_tool_candidates(tmp_path: Path) -> None:
    zenmux = FakeProvider(
        "zenmux",
        models=[free_model("qwen/qwen3.5-plus", "zenmux")],
        failures={
            "qwen/qwen3.5-plus": [
                NormalizedProviderError(
                    "quota_exhausted",
                    "credit required",
                    provider="zenmux",
                    backend_model="qwen/qwen3.5-plus",
                    retryable=False,
                    details={"model_scoped": True},
                )
            ]
        },
    )
    go = FakeProvider("opencode-go", models=[paid_messages_tool_model("qwen3.5-plus", "opencode-go")])
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="deepseek-v4-pro", description="deepseek"),
            AliasConfig(name="minimax-m2.7", description="minimax"),
            AliasConfig(name="qwen3.5-plus", description="qwen"),
        ),
    )
    service = make_service(tmp_path, providers={"zenmux": zenmux, "opencode-go": go}, config=config)
    client = TestClient(create_app(service=service, config=service.config))

    routes = client.get("/debug/routes/qwen3.5-plus", params={"shape_key": "tools"}).json()
    assert ("opencode-go", "qwen3.5-plus") in {
        (candidate["provider_name"], candidate["backend_model"]) for candidate in routes["candidates"]
    }

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3.5-plus",
            "messages": [{"role": "user", "content": "call the tool"}],
            "tools": [{"type": "function", "function": {"name": "ping", "parameters": {"type": "object"}}}],
            "tool_choice": "auto",
        },
    )

    assert response.status_code == 200
    assert zenmux.calls == ["qwen/qwen3.5-plus"]
    assert go.calls == ["qwen3.5-plus"]


def test_nested_multimodal_input_models_are_not_exposed(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="deepseek-v4-pro", description="deepseek"),
            AliasConfig(name="minimax-m2.7", description="minimax"),
            AliasConfig(name="qwen3.5-plus", description="qwen"),
        ),
    )
    service = make_service(
        tmp_path,
        providers={
            "zenmux": FakeProvider("zenmux", models=[free_model("qwen/qwen3.5-plus", "zenmux")]),
            "opencode-go": FakeProvider("opencode-go", models=[paid_nested_multimodal_model("qwen3.5-plus", "opencode-go")]),
        },
        config=config,
    )
    client = TestClient(create_app(service=service, config=service.config))

    models = client.get("/v1/models").json()["data"]
    assert "qwen3.5-plus" not in {item["id"] for item in models}


def test_model_auth_failure_does_not_cooldown_successful_fallback_provider(tmp_path: Path) -> None:
    zenmux = FakeProvider(
        "zenmux",
        models=[free_model("minimax/minimax-m2.5", "zenmux"), free_model("minimax/minimax-m2.7", "zenmux")],
        failures={
            "minimax/minimax-m2.5": [
                NormalizedProviderError(
                    "quota_exhausted",
                    "credit required",
                    provider="zenmux",
                    backend_model="minimax/minimax-m2.5",
                    retryable=False,
                    details={"model_scoped": True},
                )
            ],
            "minimax/minimax-m2.7": [
                NormalizedProviderError(
                    "quota_exhausted",
                    "credit required",
                    provider="zenmux",
                    backend_model="minimax/minimax-m2.7",
                    retryable=False,
                    details={"model_scoped": True},
                )
            ],
        },
    )
    go = FakeProvider(
        "opencode-go",
        models=[paid_model("minimax-m2.5", "opencode-go"), paid_model("minimax-m2.7", "opencode-go")],
        failures={
            "minimax-m2.5": [
                NormalizedProviderError(
                    "unauthorized",
                    "invalid model key",
                    provider="opencode-go",
                    backend_model="minimax-m2.5",
                    retryable=False,
                    details={"message": "invalid model key"},
                )
            ]
        },
    )
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="deepseek-v4-pro", description="deepseek"),
            AliasConfig(name="minimax-m2.5", description="minimax"),
            AliasConfig(name="minimax-m2.7", description="minimax"),
        ),
    )
    service = make_service(tmp_path, providers={"zenmux": zenmux, "opencode-go": go}, config=config)
    client = TestClient(create_app(service=service, config=service.config))

    assert client.post("/v1/chat/completions", json=simple_chat_payload("minimax-m2.7")).status_code == 200
    assert client.post("/v1/chat/completions", json=simple_chat_payload("minimax-m2.5")).status_code == 424
    response = client.post("/v1/chat/completions", json=simple_chat_payload("minimax-m2.7"))

    assert response.status_code == 200
    assert response.headers["x-ghostship-router-backend-provider"] == "opencode-go"


def test_models_endpoint_hides_models_with_no_live_candidates(tmp_path: Path) -> None:
    go = FakeProvider("opencode-go", models=[paid_model("minimax-m2.5", "opencode-go")])
    config = make_config(
        tmp_path,
        aliases=(
            AliasConfig(name="deepseek-v4-pro", description="deepseek"),
            AliasConfig(name="minimax-m2.5", description="minimax"),
        ),
    )
    service = make_service(
        tmp_path,
        providers={
            "zenmux": FakeProvider("zenmux", models=[free_model("minimax/minimax-m2.5", "zenmux")]),
            "opencode-go": go,
        },
        config=config,
    )
    service.state_store.apply_failure("opencode-go", "minimax-m2.5", category="unauthorized", retryable=False)
    service.state_store.apply_failure("zenmux", "minimax/minimax-m2.5", category="quota_exhausted", retryable=False)
    client = TestClient(create_app(service=service, config=service.config))

    models = client.get("/v1/models").json()["data"]

    assert "minimax-m2.5" not in {item["id"] for item in models}


def test_tool_request_skips_endpoint_family_without_tool_adapter(tmp_path: Path) -> None:
    messages_family = free_model("deepseek-v4-pro", "opencode-zen")
    messages_family.metadata["endpoint_family"] = "messages"
    zen = FakeProvider("opencode-zen", models=[messages_family])
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"opencode-zen": zen, "opencode-go": go})

    _, headers = service.chat_completions(
        ChatCompletionRequest.model_validate(
            {
                "model": "deepseek-v4-pro",
                "messages": [{"role": "user", "content": "call the tool"}],
                "tools": [{"type": "function", "function": {"name": "ping", "parameters": {"type": "object"}}}],
            }
        )
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert zen.calls == []
    assert go.calls == ["deepseek-v4-pro"]


def test_xml_tool_call_text_is_failed_and_falls_back(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    nvidia.responses["deepseek-ai/deepseek-v4-pro"] = [
        {
            "id": "chatcmpl-bad",
            "object": "chat.completion",
            "model": "deepseek-ai/deepseek-v4-pro",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "<tool_call name=\"skill_view\"></tool_call>"},
                    "finish_reason": "stop",
                }
            ],
        }
    ]
    go = FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")])
    service = make_service(tmp_path, providers={"nvidia-build": nvidia, "opencode-go": go})

    payload, headers = service.chat_completions(
        ChatCompletionRequest.model_validate(
            {
                "model": "deepseek-v4-pro",
                "messages": [{"role": "user", "content": "call the tool"}],
                "tools": [{"type": "function", "function": {"name": "skill_view", "parameters": {"type": "object"}}}],
            }
        )
    )

    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-go"
    assert payload["choices"][0]["message"]["content"] == "deepseek-v4-pro"
    events = service.state_store.get_recent_events(10)
    assert any(event["category"] == "tool_protocol_mismatch" for event in events)


def test_streaming_tool_request_uses_guarded_synthetic_stream(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("deepseek-ai/deepseek-v4-pro", "nvidia-build")])
    nvidia.responses["deepseek-ai/deepseek-v4-pro"] = [
        {
            "id": "chatcmpl-tool",
            "object": "chat.completion",
            "model": "deepseek-ai/deepseek-v4-pro",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "skill_view", "arguments": "{\"name\":\"ghostship-media-services-health\"}"},
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
        }
    ]
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": nvidia,
            "opencode-go": FakeProvider("opencode-go", models=[paid_model("deepseek-v4-pro", "opencode-go")]),
        },
    )

    plan = service.stream_chat_completions(
        ChatCompletionRequest.model_validate(
            {
                "model": "deepseek-v4-pro",
                "stream": True,
                "messages": [{"role": "user", "content": "call the tool"}],
                "tools": [{"type": "function", "function": {"name": "skill_view", "parameters": {"type": "object"}}}],
            }
        )
    )
    body = "".join(plan.body)

    assert '"tool_calls"' in body
    assert "<tool_call" not in body


def test_request_shape_errors_do_not_apply_model_cooldown() -> None:
    for category in ("bad_request", "tool_choice_unsupported"):
        exc = NormalizedProviderError(
            category,
            "request shape is unsupported",
            provider="opencode-go",
            backend_model="deepseek-v4-pro",
            retryable=False,
        )
        assert RouterService._should_apply_model_cooldown(exc) is False


def test_model_scoped_exhaustion_applies_model_cooldown() -> None:
    exc = NormalizedProviderError(
        "quota_exhausted",
        "credit required for this model",
        provider="zenmux",
        backend_model="deepseek/deepseek-v4-pro",
        retryable=False,
        details={"model_scoped": True},
    )

    assert RouterService._should_apply_model_cooldown(exc) is True


def test_all_candidates_bad_request_returns_failed_dependency(tmp_path: Path) -> None:
    zenmux = FakeProvider(
        "zenmux",
        models=[free_model("deepseek/deepseek-v4-pro-free", "zenmux")],
        failures={
            "deepseek/deepseek-v4-pro-free": [
                NormalizedProviderError(
                    "bad_request",
                    "The `reasoning_content` in the thinking mode must be passed back to the API.",
                    provider="zenmux",
                    backend_model="deepseek/deepseek-v4-pro-free",
                    retryable=False,
                )
            ]
        },
    )
    go = FakeProvider(
        "opencode-go",
        models=[paid_model("deepseek-v4-pro", "opencode-go")],
        failures={
            "deepseek-v4-pro": [
                NormalizedProviderError(
                    "bad_request",
                    "The `reasoning_content` in the thinking mode must be passed back to the API.",
                    provider="opencode-go",
                    backend_model="deepseek-v4-pro",
                    retryable=False,
                )
            ]
        },
    )
    service = make_service(tmp_path, providers={"zenmux": zenmux, "opencode-go": go})
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post("/v1/chat/completions", json={"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hello"}]})

    assert response.status_code == 424
