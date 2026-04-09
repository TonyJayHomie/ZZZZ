"""
OpenAI-compatible request/response Pydantic models.
These schemas let any OpenAI client (OpenClaw, etc.) talk to our bridge.
"""

import time
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "claude-sonnet-4-6"
    messages: list[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[list[str] | str] = None


# =============================================================================
# Response Models (non-streaming)
# =============================================================================


class Choice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "claude-sonnet-4-6"
    choices: list[Choice]
    usage: Usage = Field(default_factory=Usage)


# =============================================================================
# Streaming Response Models (SSE chunks)
# =============================================================================


class DeltaContent(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: DeltaContent
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "claude-sonnet-4-6"
    choices: list[StreamChoice]


# =============================================================================
# Models List
# =============================================================================


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "anthropic"


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


# Available models exposed by the wrapper
AVAILABLE_MODELS = ModelList(
    data=[
        ModelInfo(id="claude-opus-4-6"),
        ModelInfo(id="claude-sonnet-4-6"),
        ModelInfo(id="claude-haiku-4-5"),
        ModelInfo(id="claude-opus-4-5"),
        ModelInfo(id="claude-sonnet-4-5"),
    ]
)
