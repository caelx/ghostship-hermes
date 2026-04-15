from __future__ import annotations

import json

import httpx
import pytest

from hermes_router.providers.base import NormalizedProviderError
from hermes_router.providers.nvidia_build import NvidiaBuildProvider


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_list_models_returns_curated_free_inventory() -> None:
    provider = NvidiaBuildProvider(
        "secret",
        models=(
            "moonshotai/kimi-k2-instruct",
            "mistralai/mistral-nemotron",
            "deepseek-ai/deepseek-r1",
        ),
        base_url="https://integrate.api.nvidia.com/v1",
    )

    models = provider.list_models()

    assert [model.id for model in models] == [
        "moonshotai/kimi-k2-instruct",
        "mistralai/mistral-nemotron",
        "deepseek-ai/deepseek-r1",
    ]
    assert all(model.provider == "nvidia-build" for model in models)
    assert all(model.is_free is True for model in models)


def test_chat_completion_strips_stream_flag_before_sync_request() -> None:
    seen_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content.decode())
        seen_bodies.append(body)
        assert "stream" not in body
        assert body["model"] == "mistralai/mistral-nemotron"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "model": "mistralai/mistral-nemotron",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            },
        )

    provider = NvidiaBuildProvider(
        "secret",
        models=("mistralai/mistral-nemotron",),
        base_url="https://integrate.api.nvidia.com/v1",
        transport=make_transport(handler),
    )
    result = provider.chat_completions(
        "mistralai/mistral-nemotron",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    assert result.payload["choices"][0]["message"]["content"] == "ok"
    assert len(seen_bodies) == 1


def test_nvidia_retry_after_marks_provider_pacing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            429,
            headers={"Retry-After": "9"},
            json={"error": {"message": "Rate limit exceeded. Please retry later."}},
        )

    provider = NvidiaBuildProvider(
        "secret",
        models=("mistralai/mistral-nemotron",),
        base_url="https://integrate.api.nvidia.com/v1",
        transport=make_transport(handler),
    )
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions("mistralai/mistral-nemotron", {"messages": [{"role": "user", "content": "hello"}]})
    exc = excinfo.value
    assert exc.category == "rate_limited"
    assert exc.details["temporary_throttle"] is True
    assert exc.details["provider_pacing"] is True
    assert exc.details["retry_after_seconds"] == 9
