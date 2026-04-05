from __future__ import annotations

from .base import ChatProvider, ProviderChatResult, ProviderModel


class GeminiFallbackAdapter:
    name = "gemini-fallback"

    def __init__(self, backend: ChatProvider, *, model_id: str):
        self.backend = backend
        self.model_id = model_id

    def list_models(self, *, timeout: float | None = None) -> list[ProviderModel]:
        return [
            ProviderModel(
                id=self.model_id,
                provider=self.name,
                is_free=False,
                tags=("heavyweight",),
                metadata={"fallback": "gemini"},
            )
        ]

    def chat_completions(self, backend_model: str, payload: dict[str, object], *, timeout: float | None = None) -> ProviderChatResult:
        model_id = self.model_id if backend_model == self.model_id else backend_model
        result = self.backend.chat_completions(model_id, payload, timeout=timeout)
        return ProviderChatResult(payload=result.payload, provider=self.name, backend_model=result.backend_model)
