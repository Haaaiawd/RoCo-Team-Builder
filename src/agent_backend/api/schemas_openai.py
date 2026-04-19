from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImageUrlPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    detail: str | None = None


class TextContentPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"]
    text: str


class ImageContentPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["image_url"]
    image_url: ImageUrlPayload


ChatContentPart = Annotated[
    TextContentPart | ImageContentPart,
    Field(discriminator="type"),
]


class ChatMessagePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: str | list[ChatContentPart] | None = None


class ChatCompletionsRequestPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatMessagePayload]
    stream: bool = False
    max_tokens: int | None = None

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, value: list[ChatMessagePayload]) -> list[ChatMessagePayload]:
        if not value:
            raise ValueError("messages required")
        return value


class OpenAIErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    type: str
    param: str | None = None
    code: str | None = None
    metadata: dict[str, Any] | None = None


class OpenAIErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: OpenAIErrorPayload
