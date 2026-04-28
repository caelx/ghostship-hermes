from __future__ import annotations

import pytest
import httpx

from hermes_router.providers.base import NormalizedProviderError
from hermes_router.providers.openrouter import OpenRouterProvider
from hermes_router.providers.opencode_zen import OpencodeZenProvider


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_openrouter_temporary_upstream_rate_limit_marks_provider_pacing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/chat/completions"
        return httpx.Response(
            429,
            headers={"Retry-After": "11"},
            json={"error": {"message": "This model is temporarily rate-limited upstream. Please retry shortly."}},
        )

    provider = OpenRouterProvider("secret", base_url="https://openrouter.example/api/v1", transport=make_transport(handler))
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions("qwen/qwen3-coder:free", {"messages": [{"role": "user", "content": "hello"}]})
    exc = excinfo.value
    assert exc.category == "rate_limited"
    assert exc.details["temporary_throttle"] is True
    assert exc.details["provider_pacing"] is True
    assert exc.details["retry_after_seconds"] == 11


def test_opencode_zen_free_usage_limit_captures_retry_after() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/chat/completions", "/v1/chat/completions"}
        return httpx.Response(
            429,
            headers={"Retry-After": "35"},
            json={"type": "FreeUsageLimitError", "message": "Rate limit exceeded. Please try again later."},
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode.example/v1", transport=make_transport(handler))
    provider._family_cache["minimax-m2.5-free"] = "chat_completions"
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions("minimax-m2.5-free", {"messages": [{"role": "user", "content": "hello"}]})
    exc = excinfo.value
    assert exc.category == "rate_limited"
    assert exc.details["temporary_throttle"] is True
    assert exc.details["provider_pacing"] is True
    assert exc.details["retry_after_seconds"] == 35


def test_opencode_zen_payment_required_is_balance_exhaustion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/chat/completions", "/v1/chat/completions"}
        return httpx.Response(
            402,
            json={"error": {"message": "Payment Required"}},
        )

    provider = OpencodeZenProvider("secret", base_url="https://zenmux.example/v1", transport=make_transport(handler), provider_name="zenmux")
    provider._family_cache["minimax/minimax-m2.7"] = "chat_completions"
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions("minimax/minimax-m2.7", {"messages": [{"role": "user", "content": "hello"}]})
    exc = excinfo.value
    assert exc.category == "insufficient_balance"
    assert exc.details["hard_exhaustion"] is True
    assert exc.retryable is False


def test_opencode_zen_model_scoped_payment_required_is_model_exhaustion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/chat/completions", "/v1/chat/completions"}
        return httpx.Response(
            402,
            json={"error": {"message": "Credit required. To prevent abuse, a positive balance is required for this model."}},
        )

    provider = OpencodeZenProvider("secret", base_url="https://zenmux.example/v1", transport=make_transport(handler), provider_name="zenmux")
    provider._family_cache["deepseek/deepseek-v4-pro"] = "chat_completions"
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions("deepseek/deepseek-v4-pro", {"messages": [{"role": "user", "content": "hello"}]})
    exc = excinfo.value
    assert exc.category == "quota_exhausted"
    assert exc.details["model_scoped"] is True
    assert exc.details.get("hard_exhaustion") is not True
    assert exc.retryable is False


def test_opencode_go_tool_choice_unsupported_is_classified_separately() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path in {"/chat/completions", "/v1/chat/completions"}
        return httpx.Response(
            400,
            json={"error": {"message": "Error from provider (DeepSeek): deepseek-reasoner does not support this tool_choice"}},
        )

    provider = OpencodeZenProvider("secret", base_url="https://opencode-go.example/v1", transport=make_transport(handler), provider_name="opencode-go")
    provider._family_cache["deepseek-v4-pro"] = "chat_completions"
    with pytest.raises(NormalizedProviderError) as excinfo:
        provider.chat_completions(
            "deepseek-v4-pro",
            {
                "messages": [{"role": "user", "content": "hello"}],
                "tools": [{"type": "function", "function": {"name": "skill_view"}}],
                "tool_choice": {"type": "function", "function": {"name": "skill_view"}},
            },
        )
    exc = excinfo.value
    assert exc.category == "tool_choice_unsupported"
    assert exc.retryable is False
