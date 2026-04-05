from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderModel:
    id: str
    provider: str
    is_free: bool
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderChatResult:
    payload: dict[str, Any]
    provider: str
    backend_model: str
    first_text_latency_ms: float | None = None


@dataclass
class ProviderChatStreamState:
    first_text_latency_ms: float | None = None
    usage: dict[str, Any] | None = None
    final_payload: dict[str, Any] | None = None
    emitted_text: str = ""


@dataclass(frozen=True)
class ProviderChatStreamResult:
    chunks: Iterator[str]
    provider: str
    backend_model: str
    state: ProviderChatStreamState


class NormalizedProviderError(Exception):
    def __init__(self, category: str, message: str, *, provider: str, backend_model: str | None = None, retryable: bool = False, details: Any = None):
        super().__init__(message)
        self.category = category
        self.provider = provider
        self.backend_model = backend_model
        self.retryable = retryable
        self.details = details


class ChatProvider(Protocol):
    name: str

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        ...

    def chat_completions(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatResult:
        ...

    def chat_completions_stream(self, backend_model: str, payload: dict[str, Any], *, timeout: float | None = None) -> ProviderChatStreamResult:
        ...
