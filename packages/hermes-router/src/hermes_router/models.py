from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Any
    name: str | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: float | None = None


class ResponsesRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = "agentic"
    input: Any
    instructions: str | None = None
    previous_response_id: str | None = None
    conversation: str | None = None
    store: bool = True
    stream: bool = False
    truncation: str | None = None
    timeout: float | None = None


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "ghostship-hermes-router"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelCard]


class HealthResponse(BaseModel):
    ok: bool


class HealthStatusResponse(BaseModel):
    status: str
    platform: str


class ReadinessResponse(BaseModel):
    ok: bool
    providers: list[str]
    detail: str
