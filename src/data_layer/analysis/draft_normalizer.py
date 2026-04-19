"""
Team Draft Normalizer — 归一化 TeamDraft 输入。

剥离前端 UI 暂态字段，只保留共享领域字段。
对齐: data-layer-system.detail.md §3.6 队伍分析输入被 UI 暂态污染
"""

from __future__ import annotations

from typing import Any

from ..app.contracts import TeamDraft
from ..app.errors import TeamAnalysisInputError


# UI 暂态字段白名单 — 这些字段应被剥离，不进入分析计算
UI_TRANSIENT_FIELDS = {
    "loading",
    "selected",
    "expanded",
    "dirty",
    "editing",
    "ui_state",
    "scroll_position",
    "last_updated_at",
}

# 共享领域字段白名单 — 只有这些字段会被保留
SHARED_DOMAIN_FIELDS = {
    "slot_index",
    "spirit_name",
    "skills",
}


def normalize_team_draft(team_draft: dict | TeamDraft) -> dict:
    """归一化 TeamDraft，剥离前端 UI 暂态字段。

    Args:
        team_draft: 原始 TeamDraft 对象（dict 或 TeamDraft 实例）

    Returns:
        归一化后的槽位列表，每个槽位只包含共享领域字段

    Raises:
        TeamAnalysisInputError: 当输入格式无效或 schema_version 不匹配时
    """
    if isinstance(team_draft, TeamDraft):
        draft_dict = {
            "schema_version": team_draft.schema_version,
            "slots": team_draft.slots,
        }
    else:
        draft_dict = team_draft

    # 验证 schema_version
    schema_version = draft_dict.get("schema_version")
    if not schema_version:
        raise TeamAnalysisInputError(
            "TeamDraft missing required field: schema_version"
        )
    if schema_version != "v1":
        raise TeamAnalysisInputError(
            f"Unsupported schema_version: {schema_version}. Expected: v1"
        )

    # 验证 slots 字段
    slots = draft_dict.get("slots")
    if not isinstance(slots, list):
        raise TeamAnalysisInputError(
            "TeamDraft.slots must be a list"
        )

    # 归一化每个槽位
    normalized_slots = []
    for slot in slots:
        if not isinstance(slot, dict):
            raise TeamAnalysisInputError(
                f"TeamDraft slot must be a dict, got {type(slot)}"
            )

        # 验证 slot_index
        slot_index = slot.get("slot_index")
        if slot_index is None:
            raise TeamAnalysisInputError(
                "TeamDraft slot missing required field: slot_index"
            )

        # 只保留共享领域字段
        normalized_slot = {
            "slot_index": slot_index,
            "spirit_name": slot.get("spirit_name"),
            "skills": slot.get("skills", []),
        }

        normalized_slots.append(normalized_slot)

    return {"slots": normalized_slots, "schema_version": schema_version}


def build_team_fingerprint(slots: list[dict]) -> str:
    """构建队伍指纹，用于缓存键。

    Args:
        slots: 归一化后的槽位列表

    Returns:
        队伍指纹字符串
    """
    # 按槽位排序，确保相同队伍产生相同指纹
    sorted_slots = sorted(slots, key=lambda s: s["slot_index"])

    # 提取精灵名和技能签名
    spirit_signatures = []
    for slot in sorted_slots:
        spirit_name = slot.get("spirit_name") or ""
        skills = slot.get("skills", [])
        skill_names = sorted([s.get("name", "") for s in skills if isinstance(s, dict)])
        signature = f"{spirit_name}:{','.join(skill_names)}"
        spirit_signatures.append(signature)

    return "|".join(spirit_signatures)
