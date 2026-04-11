from __future__ import annotations

import uuid
from typing import Any

from pydantic import ValidationError

from ..api import error_mapping
from ..api.schemas_openai import ChatCompletionsRequestPayload, ChatMessagePayload
from .model_catalog import ModelCatalog
from .request_context import ChatRequestContext
from .session_service import SessionIdentityError, resolve_session_key

REQUEST_LIMITS = {
    "max_messages": 40,
    "max_text_chars": 20000,
    "max_total_image_url_chars": 200000,
    "max_tokens": 8192,
}


def normalize_chat_request(
    payload: dict[str, Any],
    headers: dict[str, str],
    catalog: ModelCatalog,
) -> ChatRequestContext:
    try:
        parsed = ChatCompletionsRequestPayload.model_validate(payload)
    except ValidationError as exc:
        raise error_mapping.from_validation_exception(exc) from exc

    model_entry = catalog.get(parsed.model)
    if model_entry is None or not model_entry.enabled:
        raise error_mapping.model_not_found(parsed.model)

    _validate_request_limits(parsed.messages, parsed.max_tokens)

    if _contains_image_part(parsed.messages) and not model_entry.supports_vision:
        raise error_mapping.capability_vision_unsupported()

    try:
        session_key = resolve_session_key(headers)
    except SessionIdentityError as exc:
        raise error_mapping.from_session_identity_error(exc) from exc

    normalized_headers = {str(k): str(v) for k, v in headers.items()}
    user_id = normalized_headers.get("x-openwebui-user-id") or normalized_headers.get(
        "X-OpenWebUI-User-Id", ""
    )
    chat_id = normalized_headers.get("x-openwebui-chat-id") or normalized_headers.get(
        "X-OpenWebUI-Chat-Id"
    )

    return ChatRequestContext(
        request_id=f"req_{uuid.uuid4().hex}",
        session_key=session_key,
        model_entry=model_entry,
        messages=[message.model_dump(mode="python") for message in parsed.messages],
        stream=parsed.stream,
        user_id=user_id,
        chat_id=chat_id,
        request_headers=normalized_headers,
    )


def _validate_request_limits(messages: list[ChatMessagePayload], max_tokens: int | None) -> None:
    if len(messages) > REQUEST_LIMITS["max_messages"]:
        raise error_mapping.payload_too_large("消息条数过多，请开启新对话")

    total_text_chars = 0
    total_image_url_chars = 0

    for message in messages:
        content = message.content
        if isinstance(content, str):
            total_text_chars += len(content)
            continue
        if not isinstance(content, list):
            continue
        for part in content:
            if part.type == "text":
                total_text_chars += len(part.text)
            elif part.type == "image_url":
                total_image_url_chars += len(part.image_url.url)

    if total_text_chars > REQUEST_LIMITS["max_text_chars"]:
        raise error_mapping.payload_too_large("文本输入过长，请缩短后重试")

    if total_image_url_chars > REQUEST_LIMITS["max_total_image_url_chars"]:
        raise error_mapping.payload_too_large("图片内容过大，请减少图片或改用外链")

    if max_tokens is not None and max_tokens > REQUEST_LIMITS["max_tokens"]:
        raise error_mapping.payload_too_large("max_tokens 超出当前允许范围")


def _contains_image_part(messages: list[ChatMessagePayload]) -> bool:
    for message in messages:
        content = message.content
        if not isinstance(content, list):
            continue
        for part in content:
            if part.type == "image_url":
                return True
    return False
