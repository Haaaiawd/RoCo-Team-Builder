"""
能力守卫 — 后端最终能力兜底。

职责：
- 检查模型是否支持视觉（supports_vision）
- 图片请求命中不支持视觉的模型时返回 CAPABILITY_ 错误
- 区分 CAPABILITY_ 与 Provider 原生错误

对齐: agent-backend-system.md §3.5 错误矩阵、§4 能力兜底
验收标准: T3.3.1 图片请求命中不支持视觉的模型返回 CAPABILITY_ 错误
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class CapabilityDecision(Enum):
    """能力决策结果。"""

    ALLOWED = "allowed"
    CAPABILITY_MISMATCH = "capability_mismatch"


def check_vision_capability(
    context: dict[str, Any],
    model_supports_vision: bool,
) -> CapabilityDecision:
    """检查视觉能力是否匹配。

    对齐: agent-backend-system.md §5.1 视觉能力兜底

    Args:
        context: ChatRequestContext（简化为 dict）
        model_supports_vision: 模型是否支持视觉

    Returns:
        CapabilityDecision.ALLOWED 或 CapabilityDecision.CAPABILITY_MISMATCH
    """
    # 检查请求是否包含图片
    has_image = False
    messages = context.get("messages", [])
    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    has_image = True
                    break
        if has_image:
            break

    # 如果有图片但模型不支持视觉，返回能力不匹配
    if has_image and not model_supports_vision:
        return CapabilityDecision.CAPABILITY_MISMATCH

    return CapabilityDecision.ALLOWED
