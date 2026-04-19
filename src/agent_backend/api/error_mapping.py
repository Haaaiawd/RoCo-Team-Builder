from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .schemas_openai import OpenAIErrorPayload, OpenAIErrorResponse
from ..app.session_service import SessionIdentityError


@dataclass(slots=True)
class ProductError(Exception):
    code: str
    message: str
    status_code: int
    error_type: str = "invalid_request_error"
    param: str | None = None
    retryable: bool = False
    metadata: dict[str, Any] | None = None

    def to_response(self) -> JSONResponse:
        payload = OpenAIErrorResponse(
            error=OpenAIErrorPayload(
                message=self.message,
                type=self.error_type,
                param=self.param,
                code=self.code,
                metadata={
                    **(self.metadata or {}),
                    "retryable": self.retryable,
                },
            )
        )
        return JSONResponse(status_code=self.status_code, content=payload.model_dump())


def model_not_found(model_id: str) -> ProductError:
    return ProductError(
        code="MODEL_NOT_FOUND",
        message=f"模型不可用: {model_id}",
        status_code=404,
        param="model",
    )


def capability_vision_unsupported() -> ProductError:
    return ProductError(
        code="CAPABILITY_VISION_UNSUPPORTED",
        message="当前模型不支持截图识别，请切换支持视觉的模型或切回内置轨道",
        status_code=400,
        param="messages",
        retryable=True,
    )


def validation_error(message: str, *, param: str | None = None) -> ProductError:
    return ProductError(
        code="VALIDATION_INVALID_REQUEST",
        message=message,
        status_code=400,
        param=param,
    )


def payload_too_large(message: str = "输入内容过大，请缩短消息或减少图片内容") -> ProductError:
    return ProductError(
        code="VALIDATION_PAYLOAD_TOO_LARGE",
        message=message,
        status_code=400,
        param="messages",
    )


def from_validation_exception(exc: ValidationError) -> ProductError:
    first = exc.errors()[0] if exc.errors() else {"msg": "invalid request", "loc": []}
    location = first.get("loc") or []
    param = ".".join(str(item) for item in location if item != "body") or None
    return validation_error(first.get("msg", "invalid request"), param=param)


def from_session_identity_error(exc: SessionIdentityError) -> ProductError:
    return ProductError(
        code=exc.error_code,
        message=exc.message,
        status_code=400,
        param="headers",
    )
