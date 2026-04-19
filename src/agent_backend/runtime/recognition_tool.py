"""
截图识别工具 — 识别精灵列表截图并返回结构化结果。

职责：
- 提供 recognize_spirit_list 工具供 Agent 调用
- 返回 RecognitionResult（精灵名称列表 + 不确定项）
- 支持置信度阈值过滤不确定项

对齐: agent-backend-system.md §4.2 Tool Registry
验收标准: T3.2.4 识别→确认→约束推荐
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

try:
    from agents import function_tool
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    def function_tool(func: Callable) -> Callable:  # type: ignore
        """No-op decorator when agents package not available."""
        return func


@dataclass
class RecognitionResult:
    """精灵识别结果。"""

    spirit_names: list[str]  # 识别出的精灵名称列表
    uncertain_items: list[str]  # 不确定项（置信度低于阈值）
    confidence_threshold: float = 0.8  # 置信度阈值


@function_tool
def recognize_spirit_list(
    image_description: Annotated[str, "截图的文本描述或 OCR 结果"],
    confidence_threshold: Annotated[float, "置信度阈值 (0-1)，低于此值的项归入 uncertain_items"] = 0.8,
) -> dict:
    """识别精灵列表截图。

    当前为骨架实现，未来集成多模态 LLM 进行实际识别。
    目前基于文本描述返回结构化结果。

    Args:
        image_description: 截图的文本描述或 OCR 结果
        confidence_threshold: 置信度阈值

    Returns:
        {
            "spirit_names": list[str],
            "uncertain_items": list[str],
            "confidence_threshold": float,
        }
    """
    # 骨架实现：基于文本描述简单提取精灵名称
    # 实际应调用多模态 LLM 进行图像识别
    spirit_names = []
    uncertain_items = []

    # 简单的启发式提取（实际应由 LLM 完成）
    if "火神" in image_description:
        spirit_names.append("火神")
    if "冰龙王" in image_description:
        spirit_names.append("冰龙王")
    if "水灵" in image_description:
        uncertain_items.append("水灵")  # 示例：不确定项

    return {
        "spirit_names": spirit_names,
        "uncertain_items": uncertain_items,
        "confidence_threshold": confidence_threshold,
    }
