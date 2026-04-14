from __future__ import annotations

import json

import httpx

from hermes_router.providers.opencode_zen import OpencodeZenProvider


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_list_models_infers_endpoint_family_and_free_status(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {"id": "big-pickle", "object": "model", "created": 1, "owned_by": "opencode"},
                    {"id": "claude-sonnet-4-6", "object": "model", "created": 1, "owned_by": "opencode"},
                    {"id": "gemini-3-flash", "object": "model", "created": 1, "owned_by": "opencode"},
                    {"id": "gpt-5.4-mini", "object": "model", "created": 1, "owned_by": "opencode"},
                ],
            },
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    monkeypatch.setattr(
        provider,
        "_fetch_public_metadata",
        lambda timeout=None: {
            "big-pickle": {"cost": {"input": 0, "output": 0}},
            "gpt-5.4-mini": {"cost": {"input": 0.75, "output": 4.5}},
        },
    )
    models = provider.list_models()
    by_id = {model.id: model for model in models}
    assert by_id["big-pickle"].is_free is True
    assert by_id["claude-sonnet-4-6"].metadata["endpoint_family"] == "messages"
    assert by_id["gemini-3-flash"].metadata["endpoint_family"] == "google_generate_content"
    assert by_id["gpt-5.4-mini"].metadata["endpoint_family"] == "responses"


def test_chat_completion_probes_next_family_on_mismatch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/responses":
            return httpx.Response(
                401,
                json={"type": "error", "error": {"type": "ModelError", "message": "Model minimax-m2.5-free not supported for format openai"}},
            )
        if request.url.path == "/v1/responses":
            return httpx.Response(
                401,
                json={"type": "error", "error": {"type": "ModelError", "message": "Model minimax-m2.5-free not supported for format openai"}},
            )
        if request.url.path == "/chat/completions":
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "model": "minimax-m2.5-free",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
                },
            )
        if request.url.path == "/v1/chat/completions":
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "model": "minimax-m2.5-free",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["minimax-m2.5-free"] = "responses"
    result = provider.chat_completions(
        "minimax-m2.5-free",
        {"messages": [{"role": "user", "content": "hello"}], "max_tokens": 8},
    )
    assert result.payload["choices"][0]["message"]["content"] == "ok"
    assert provider._family_cache["minimax-m2.5-free"] == "chat_completions"


def test_chat_completion_normalizes_messages_and_google_families() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path in {"/messages", "/v1/messages"}:
            body = json.loads(request.content.decode())
            assert body["model"] == "claude-sonnet-4-6"
            return httpx.Response(
                200,
                json={
                    "id": "msg_1",
                    "content": [{"type": "text", "text": "claude ok"}],
                    "stop_reason": "end_turn",
                },
            )
        if request.url.path in {"/models/gemini-3-flash:generateContent", "/v1/models/gemini-3-flash:generateContent"}:
            body = json.loads(request.content.decode())
            assert body["contents"][0]["parts"][0]["text"] == "hello"
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "gemini ok"}]}}]},
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    claude = provider.chat_completions("claude-sonnet-4-6", {"messages": [{"role": "user", "content": "hello"}]})
    gemini = provider.chat_completions("gemini-3-flash", {"messages": [{"role": "user", "content": "hello"}]})
    assert claude.payload["choices"][0]["message"]["content"] == "claude ok"
    assert gemini.payload["choices"][0]["message"]["content"] == "gemini ok"
    assert any(path.endswith("/messages") for path in seen_paths)
    assert any(path.endswith("/models/gemini-3-flash:generateContent") for path in seen_paths)


def test_chat_completion_strips_stream_flag_before_sync_request() -> None:
    seen_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path not in {"/chat/completions", "/v1/chat/completions"}:
            raise AssertionError(f"unexpected path: {request.url.path}")
        body = json.loads(request.content.decode())
        seen_bodies.append(body)
        assert "stream" not in body
        assert body["model"] == "minimax-m2.5-free"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "model": "minimax-m2.5-free",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            },
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["minimax-m2.5-free"] = "chat_completions"
    result = provider.chat_completions(
        "minimax-m2.5-free",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    assert result.payload["choices"][0]["message"]["content"] == "ok"
    assert len(seen_bodies) == 1


def test_chat_completion_stream_uses_native_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/chat/completions", "/v1/chat/completions"}
        body = json.loads(request.content.decode())
        assert body["stream"] is True
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"hel"},"finish_reason":null}]}\n\n'
                'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"lo"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["minimax-m2.5-free"] = "chat_completions"
    result = provider.chat_completions_stream(
        "minimax-m2.5-free",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    events = list(result.chunks)
    assert [event.content for event in events if event.content] == ["hel", "lo"]
    assert result.state.usage == {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    assert result.state.final_payload is not None
    assert result.state.final_payload["choices"][0]["message"]["content"] == "hello"
    assert result.state.final_payload["choices"][0]["finish_reason"] == "stop"


def test_responses_stream_uses_native_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/responses", "/v1/responses"}
        body = json.loads(request.content.decode())
        assert body["stream"] is True
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"hel"}\n\n'
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"lo"}\n\n'
                'event: response.completed\n'
                'data: {"type":"response.completed","response":{"id":"resp_1","model":"gpt-5.4-mini","output_text":"hello","usage":{"input_tokens":3,"output_tokens":2,"total_tokens":5}}}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["gpt-5.4-mini"] = "responses"
    result = provider.chat_completions_stream(
        "gpt-5.4-mini",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    events = list(result.chunks)
    assert [event.content for event in events if event.content] == ["hel", "lo"]
    assert result.state.usage == {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}
    assert result.state.final_payload is not None
    assert result.state.final_payload["choices"][0]["message"]["content"] == "hello"


def test_messages_stream_uses_native_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/messages", "/v1/messages"}
        body = json.loads(request.content.decode())
        assert body["stream"] is True
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                'event: message_start\n'
                'data: {"type":"message_start","message":{"usage":{"input_tokens":4}}}\n\n'
                'event: content_block_delta\n'
                'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"hel"}}\n\n'
                'event: content_block_delta\n'
                'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"lo"}}\n\n'
                'event: message_delta\n'
                'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"input_tokens":4,"output_tokens":2}}\n\n'
            ),
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["claude-sonnet-4-6"] = "messages"
    result = provider.chat_completions_stream(
        "claude-sonnet-4-6",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    events = list(result.chunks)
    assert [event.content for event in events if event.content] == ["hel", "lo"]
    assert any(event.finish_reason == "end_turn" for event in events)
    assert result.state.final_payload is not None
    assert result.state.final_payload["choices"][0]["message"]["content"] == "hello"
    assert result.state.final_payload["choices"][0]["finish_reason"] == "end_turn"


def test_google_stream_uses_native_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/models/gemini-3-flash:streamGenerateContent", "/v1/models/gemini-3-flash:streamGenerateContent"}
        assert request.url.params["alt"] == "sse"
        body = json.loads(request.content.decode())
        assert "stream" not in body
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                'data: {"candidates":[{"content":{"parts":[{"text":"hel"}]}}]}\n\n'
                'data: {"candidates":[{"content":{"parts":[{"text":"lo"}]},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":4,"candidatesTokenCount":2,"totalTokenCount":6}}\n\n'
            ),
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["gemini-3-flash"] = "google_generate_content"
    result = provider.chat_completions_stream(
        "gemini-3-flash",
        {"messages": [{"role": "user", "content": "hello"}], "stream": True},
    )
    events = list(result.chunks)
    assert [event.content for event in events if event.content] == ["hel", "lo"]
    assert any(event.finish_reason == "stop" for event in events)
    assert result.state.final_payload is not None
    assert result.state.final_payload["choices"][0]["message"]["content"] == "hello"
