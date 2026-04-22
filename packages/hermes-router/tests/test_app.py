from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from hermes_router.app import create_app
from hermes_router.config import AliasConfig, ProviderSelectionPolicy, RouterConfig
from hermes_router.models import ChatCompletionRequest
from hermes_router.providers.base import (
    NormalizedProviderError,
    ProviderChatResult,
    ProviderChatStreamEvent,
    ProviderChatStreamResult,
    ProviderChatStreamState,
    ProviderModel,
)
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
        ranking_enabled=False,
        ranking_interval_seconds=900,
        ranking_worker_model=None,
        ranking_shortlist_size=5,
        provider_cooldown_seconds=300,
        provider_failure_threshold=3.0,
        provider_rate_limit_threshold=2.5,
        provider_timeout_threshold=2.5,
        provider_exhaustion_threshold=3.0,
        exhaustion_cooldown_ladder_seconds=(30, 60, 300, 600),
        provider_suspect_window_seconds=120,
        provider_disable_seconds=60,
        provider_probe_escalation_factor=2.0,
        provider_max_disable_seconds=600,
        provider_lane_limit=3,
        provider_throttle_ladder_seconds=(15, 30, 60),
        openrouter_min_request_spacing_seconds=3.0,
        opencode_min_request_spacing_seconds=2.0,
        nvidia_build_min_request_spacing_seconds=1.0,
        openrouter_api_key=None,
        openrouter_base_url="https://openrouter.example/api/v1",
        openrouter_http_referer=None,
        openrouter_title=None,
        opencode_api_key=None,
        opencode_base_url="https://opencode.example/v1",
        nvidia_build_api_key=None,
        nvidia_build_base_url="https://integrate.api.nvidia.com/v1",
        assisted_bucket_model=None,
        assisted_bucket_batch_size=20,
        disabled_providers=(),
        disabled_models=(),
        provider_weight_overrides={},
        model_weight_overrides={},
        alias_pin_overrides={"agentic": ()},
        provider_priority=("nvidia-build", "opencode-zen", "openrouter"),
        provider_reserve_limit=5,
        provider_active_candidate_limit=3,
        provider_selection_policies=(
            ProviderSelectionPolicy(
                provider_name="nvidia-build",
                ranked_models=("nvidia-1", "nvidia-2", "nvidia-3", "nvidia-4", "nvidia-5"),
                unused_models=("nvidia-bad",),
            ),
            ProviderSelectionPolicy(
                provider_name="opencode-zen",
                ranked_models=("zen-1", "zen-2", "zen-3", "zen-4", "zen-5"),
            ),
            ProviderSelectionPolicy(
                provider_name="openrouter",
                ranked_models=("or-1", "or-2", "or-3", "or-4", "or-5"),
            ),
        ),
        aliases=(AliasConfig(name="agentic", description="agent", preferred_models=()),),
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

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        del timeout
        return list(self._models)

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        del payload, timeout
        self.calls.append(backend_model)
        failures = self.failures.get(backend_model) or []
        if failures:
            raise failures.pop(0)
        return ProviderChatResult(
            payload={
                "id": f"chatcmpl-{backend_model}",
                "object": "chat.completion",
                "model": backend_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": backend_model}, "finish_reason": "stop"}],
            },
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


def free_model(model_id: str, provider: str, *, tags: tuple[str, ...] = ("agentic",), modalities: tuple[str, ...] = ("text",)) -> ProviderModel:
    return ProviderModel(
        id=model_id,
        provider=provider,
        is_free=True,
        tags=tags,
        metadata={"supported_parameters": ["tools", "tool_choice"], "input_modalities": ["text"], "output_modalities": list(modalities)},
    )


def make_service(tmp_path: Path, *, providers: dict[str, FakeProvider], config: RouterConfig | None = None) -> RouterService:
    resolved = config or make_config(tmp_path)
    store = SqliteStateStore(resolved.db_path)
    service = RouterService(resolved, providers=providers, state_store=store)
    service.refresh_inventory(reason="test")
    return service


def test_models_endpoint_exposes_only_agentic_alias(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("nvidia-1", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["data"]] == ["agentic"]


def test_agentic_routes_take_top_three_currently_eligible_from_provider_top_five(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider(
                "nvidia-build",
                models=[free_model(f"nvidia-{index}", "nvidia-build") for index in range(1, 6)] + [free_model("nvidia-bad", "nvidia-build")],
            ),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("zen-1", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[free_model("or-1", "openrouter")]),
        },
    )
    service.state_store.apply_failure("nvidia-build", "nvidia-1", category="server_error", retryable=True, cooldown_model=True)

    preview = service.preview_routes("agentic")

    assert [item["backend_model"] for item in preview] == ["nvidia-2", "nvidia-3", "nvidia-4"]


def test_retryable_model_failures_do_not_cross_provider_boundary(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("nvidia-1", "nvidia-build"), free_model("nvidia-2", "nvidia-build"), free_model("nvidia-3", "nvidia-build")],
        failures={
            "nvidia-1": [NormalizedProviderError("server_error", "boom", provider="nvidia-build", backend_model="nvidia-1", retryable=True)],
            "nvidia-2": [NormalizedProviderError("server_error", "boom", provider="nvidia-build", backend_model="nvidia-2", retryable=True)],
            "nvidia-3": [NormalizedProviderError("server_error", "boom", provider="nvidia-build", backend_model="nvidia-3", retryable=True)],
        },
    )
    zen = FakeProvider("opencode-zen", models=[free_model("zen-1", "opencode-zen")])
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": nvidia,
            "opencode-zen": zen,
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )

    try:
        service.chat_completions(ChatCompletionRequest.model_validate({"model": "agentic", "messages": [{"role": "user", "content": "hello"}]}))
    except Exception as exc:
        detail = getattr(exc, "detail", {})
        assert "All route candidates failed" in str(detail.get("message"))
    else:
        raise AssertionError("expected routing failure")

    assert nvidia.calls == ["nvidia-1", "nvidia-2", "nvidia-3"]
    assert zen.calls == []


def test_quota_exhaustion_can_fail_over_to_next_provider(tmp_path: Path) -> None:
    nvidia = FakeProvider(
        "nvidia-build",
        models=[free_model("nvidia-1", "nvidia-build")],
        failures={
            "nvidia-1": [
                NormalizedProviderError(
                    "quota_exhausted",
                    "quota done",
                    provider="nvidia-build",
                    backend_model="nvidia-1",
                    retryable=False,
                    details={"hard_exhaustion": True},
                )
            ]
        },
    )
    zen = FakeProvider("opencode-zen", models=[free_model("zen-1", "opencode-zen")])
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": nvidia,
            "opencode-zen": zen,
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )

    payload, headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "agentic", "messages": [{"role": "user", "content": "hello"}]})
    )

    assert payload["choices"][0]["message"]["content"] == "zen-1"
    assert headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"


def test_session_stickiness_prefers_previous_provider_after_recovery(tmp_path: Path) -> None:
    nvidia = FakeProvider("nvidia-build", models=[free_model("nvidia-1", "nvidia-build")])
    zen = FakeProvider("opencode-zen", models=[free_model("zen-1", "opencode-zen")])
    config = make_config(tmp_path)
    store = SqliteStateStore(config.db_path)
    service = RouterService(
        config,
        providers={"nvidia-build": nvidia, "opencode-zen": zen, "openrouter": FakeProvider("openrouter", models=[])},
        state_store=store,
    )
    service.refresh_inventory(reason="test")
    service.state_store.upsert_provider_override("nvidia-build", enabled=False)

    _, first_headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "agentic", "messages": [{"role": "user", "content": "hello"}]}),
        session_id="session-1",
    )
    assert first_headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"

    service.state_store.upsert_provider_override("nvidia-build", enabled=True)
    _, second_headers = service.chat_completions(
        ChatCompletionRequest.model_validate({"model": "agentic", "messages": [{"role": "user", "content": "hello again"}]}),
        session_id="session-1",
    )
    assert second_headers["X-Ghostship-Router-Backend-Provider"] == "opencode-zen"


def test_debug_inventory_surfaces_unused_and_uncategorized_models(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider(
                "nvidia-build",
                models=[
                    free_model("nvidia-1", "nvidia-build"),
                    free_model("nvidia-bad", "nvidia-build"),
                    free_model("nvidia-extra", "nvidia-build"),
                ],
            ),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    unused = client.get("/debug/inventory/unused")
    uncategorized = client.get("/debug/inventory/uncategorized")

    assert unused.status_code == 200
    assert [item["backend_model"] for item in unused.json()["providers"]["nvidia-build"]] == ["nvidia-bad"]
    assert [item["backend_model"] for item in uncategorized.json()["providers"]["nvidia-build"]] == ["nvidia-extra"]


def test_retired_coding_alias_is_rejected(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("nvidia-1", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.post("/v1/chat/completions", json={"model": "coding", "messages": [{"role": "user", "content": "hello"}]})

    assert response.status_code == 404
    assert "retired" in response.json()["error"]["message"]


def test_debug_rankings_reports_non_routable_ranked_models_and_promotion(tmp_path: Path) -> None:
    config = make_config(
        tmp_path,
        provider_selection_policies=(
            ProviderSelectionPolicy(
                provider_name="nvidia-build",
                ranked_models=("nvidia-1", "nvidia-2", "nvidia-3", "nvidia-4", "nvidia-5"),
                unused_models=("nvidia-bad",),
            ),
            ProviderSelectionPolicy(
                provider_name="opencode-zen",
                ranked_models=("zen-1", "zen-2", "zen-3", "zen-4", "zen-5"),
            ),
            ProviderSelectionPolicy(
                provider_name="openrouter",
                ranked_models=("or-1", "or-2", "or-3", "or-4", "or-5"),
            ),
        ),
    )
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider(
                "openrouter",
                models=[
                    free_model("or-1", "openrouter"),
                    free_model("or-2", "openrouter"),
                    ProviderModel(
                        id="or-3",
                        provider="openrouter",
                        is_free=True,
                        tags=("agentic",),
                        metadata={
                            "supported_parameters": ["tools", "tool_choice"],
                            "input_modalities": ["text", "image"],
                            "output_modalities": ["text"],
                        },
                    ),
                    free_model("or-4", "openrouter"),
                    free_model("or-5", "openrouter"),
                ],
            ),
        },
    )

    payload = service.debug_rankings("agentic")
    openrouter = next(item for item in payload["providers"] if item["provider_name"] == "openrouter")
    ranked = {item["backend_model"]: item for item in openrouter["ranked"]}

    assert [item["backend_model"] for item in openrouter["active_candidates"]] == ["or-1", "or-2", "or-4"]
    assert ranked["or-1"]["score"]["reserve_bias"] > ranked["or-2"]["score"]["reserve_bias"]
    assert ranked["or-3"]["routable"] is False
    assert ranked["or-3"]["excluded_reason"] == "multimodal_input"
    assert ranked["or-4"]["active"] is True


def test_debug_summary_reports_provider_state_and_candidate_order(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="secret")
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("nvidia-1", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[free_model("zen-1", "opencode-zen")]),
            "openrouter": FakeProvider("openrouter", models=[free_model("or-1", "openrouter")]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    response = client.get("/debug/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["router"]["auth_required"] is True
    assert payload["router"]["provider_priority"] == ["nvidia-build", "opencode-zen", "openrouter"]
    assert payload["aliases"]["agentic"]["selected_provider"] == "nvidia-build"
    assert payload["providers"][0]["inventory_counts"]["ranked"] == 1


def test_configured_api_key_requires_authorization(tmp_path: Path) -> None:
    config = make_config(tmp_path, api_key="secret")
    service = make_service(
        tmp_path,
        config=config,
        providers={
            "nvidia-build": FakeProvider("nvidia-build", models=[free_model("nvidia-1", "nvidia-build")]),
            "opencode-zen": FakeProvider("opencode-zen", models=[]),
            "openrouter": FakeProvider("openrouter", models=[]),
        },
    )
    client = TestClient(create_app(service=service, config=service.config))

    unauthorized = client.get("/v1/models")
    authorized = client.get("/v1/models", headers={"Authorization": "Bearer secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
