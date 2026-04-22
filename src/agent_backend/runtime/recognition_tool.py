"""
截图识别工具 — 识别精灵列表截图并返回结构化结果。

职责：
- 提供 recognize_spirit_list 纯函数供单元测试与 Agent 运行时调用
- 返回 RecognitionResult（精灵名称列表 + 不确定项）
- 支持置信度阈值过滤不确定项

对齐: agent-backend-system.md §4.2 Tool Registry
验收标准: T3.2.4 识别→确认→约束推荐（当前为骨架实现，详见 TASKS 中 T3.2.4 的状态说明）

设计约束：
同 team_builder_tools.py：此模块只暴露"纯函数"。对 Agent 注册的
`FunctionTool` 包装集中在 `AgentFactory` 里完成，避免装饰器把函数变成
不可直接调用的 `FunctionTool` 对象。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated


@dataclass
class RecognitionResult:
    """精灵识别结果。"""

    spirit_names: list[str]
    uncertain_items: list[str]
    confidence_threshold: float = 0.8


def recognize_spirit_list(
    image_description: Annotated[str, "截图的文本描述或 OCR 结果"],
    confidence_threshold: Annotated[
        float,
        "置信度阈值 (0-1)，低于此值的项归入 uncertain_items",
    ] = 0.8,
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
    spirit_names: list[str] = []
    uncertain_items: list[str] = []

    # 骨架启发式：基于文本描述简单提取精灵名称；真实实现应由多模态 LLM 完成。
    if "火神" in image_description:
        spirit_names.append("火神")
    if "冰龙王" in image_description:
        spirit_names.append("冰龙王")
    if "水灵" in image_description:
        uncertain_items.append("水灵")

    return {
        "spirit_names": spirit_names,
        "uncertain_items": uncertain_items,
        "confidence_threshold": confidence_threshold,
    }
