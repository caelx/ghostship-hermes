from __future__ import annotations

import json

import httpx

from hermes_router.providers.openrouter import OpenRouterProvider


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_chat_completion_strips_stream_flag_before_sync_request() -> None:
    seen_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        body = json.loads(request.content.decode())
        seen_bodies.append(body)
        assert "stream" not in body
        assert body["model"] == "minimax/minimax-m2.5:free"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "model": "minimax/minimax-m2.5:free",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            },
        )

    provider = OpenRouterProvider("secret", base_url="https://openrouter.example", transport=make_transport(handler))
    result = provider.chat_completions(
        "minimax/minimax-m2.5:free",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    assert result.payload["choices"][0]["message"]["content"] == "ok"
    assert len(seen_bodies) == 1
