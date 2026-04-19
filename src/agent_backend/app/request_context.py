"""
请求上下文 — ChatRequestContext 数据类。

对齐: agent-backend-system.detail.md §2 ChatRequestContext
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model_catalog import ModelCatalogEntry


@dataclass
class ChatRequestContext:
    """归一化后的请求上下文 — 贯穿整个请求生命周期。"""

    request_id: str
    session_key: str
    model_entry: ModelCatalogEntry
    messages: list[dict[str, Any]]
    stream: bool
    user_id: str
    chat_id: str | None
    request_headers: dict[str, str] = field(default_factory=dict)

    def normalized_token_budget(self) -> int | None:
        """返回 token 预算（v2 暂不实现）。"""
        return None
