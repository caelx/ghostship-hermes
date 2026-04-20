from __future__ import annotations

import json

import httpx
import pytest

from hermes_router.providers.base import NormalizedProviderError
from hermes_router.providers.nvidia_build import NvidiaBuildProvider


def make_transport(handler):
    return httpx.MockTransport(handler)


def _catalog_html(*resources: dict[str, object]) -> str:
    blob = (
        '0:["$","$L8",null,{}]\n'
        + json.dumps(
            {
                "searchResult": {
                    "results": [
                        {
                            "totalCount": len(resources),
                            "groupValue": "_scored",
                            "resources": list(resources),
                        }
                    ]
                }
            },
            separators=(",", ":"),
        )
    )
    return f'<html><body><script>self.__next_f.push([1,{json.dumps(blob)}])</script></body></html>'


def test_list_models_discovers_current_free_inventory_from_catalog() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://build.nvidia.com/models")
        html = _catalog_html(
            {
                "orgName": "qc69jvmznzxy",
                "resourceId": "qc69jvmznzxy/minimaxai/minimax-m2.7".replace("/minimaxai/", "/"),
                "labels": [
                    {"key": "nimType", "values": ["Free Endpoint"]},
                    {"key": "publisher", "values": ["minimaxai"]},
                    {"key": "general", "values": ["coding", "reasoning", "agentic"]},
                ],
                "description": "MiniMax M2.7 is a 230B-parameter text-to-text AI model excelling in coding and reasoning.",
                "displayName": "minimax-m2.7",
                "dateCreated": "2026-04-12T01:01:05.944Z",
                "attributes": [
                    {"key": "AVAILABLE", "value": "true"},
                    {"key": "PREVIEW", "value": "false"},
                ],
                "guestAccess": True,
            },
            {
                "orgName": "qc69jvmznzxy",
                "resourceId": "qc69jvmznzxy/google/gemma-4-31b-it".replace("/google/", "/"),
                "labels": [
                    {"key": "nimType", "values": ["Deprecated Free Endpoint"]},
                    {"key": "publisher", "values": ["google"]},
                    {"key": "general", "values": ["coding", "agentic"]},
                ],
                "description": "Deprecated free route that should be filtered.",
                "displayName": "gemma-4-31b-it",
                "dateCreated": "2026-04-02T16:23:29.660Z",
                "attributes": [{"key": "AVAILABLE", "value": "true"}],
                "guestAccess": True,
            },
        )
        return httpx.Response(200, text=html)

    provider = NvidiaBuildProvider(
        "secret",
        base_url="https://integrate.api.nvidia.com/v1",
        transport=make_transport(handler),
    )

    models = provider.list_models()

    assert [model.id for model in models] == ["minimaxai/minimax-m2.7"]
    assert models[0].provider == "nvidia-build"
    assert models[0].is_free is True
    assert models[0].metadata["catalog_source"] == "build.nvidia.com/models"
    assert "agentic" in models[0].tags


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
