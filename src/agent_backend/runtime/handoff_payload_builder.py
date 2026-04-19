"""
工作台承接载荷构建器 — 从 Agent 结果生成 WorkbenchHandOffPayload。

对齐: agent-backend-system.md §5.1 build_workbench_payload
     agent-backend-system.detail.md §3.10
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..contracts.workbench import (
    ConfirmedOwnedSpiritList,
    WorkbenchHandOffPayload,
    build_empty_handoff,
)


def build_workbench_payload(
    team_draft: dict,
    team_snapshot: dict | None = None,
    wiki_targets: list[dict] | None = None,
    source: str = "agent_chat",
) -> WorkbenchHandOffPayload:
    """构建工作台承接载荷。

    对齐: agent-backend-system.detail.md §3.10

    Args:
        team_draft: 队伍草稿（必需）
        team_snapshot: 队伍分析快照（可选）
        wiki_targets: Wiki 目标列表（可选）
        source: 来源标识

    Returns:
        WorkbenchHandOffPayload 对象

    Raises:
        ValueError: team_draft 缺失必需字段时
    """
    # 验证必需字段
    if not team_draft or not isinstance(team_draft, dict):
        raise ValueError("team_draft 必须是非空 dict")

    # 检查 schema_version
    if "schema_version" not in team_draft:
        raise ValueError("team_draft 缺少 schema_version 字段")

    # 构建 wiki_targets（默认为空列表）
    targets = wiki_targets if wiki_targets is not None else []

    # 构建载荷
    payload = WorkbenchHandOffPayload(
        schema_version="v1",
        team_draft=team_draft,
        team_snapshot=team_snapshot,
        wiki_targets=targets,
        handoff_ready=True,
        source=source if source in ["agent_chat", "user_manual"] else "agent_chat",
    )

    return payload


def build_confirmed_owned_list(
    spirit_ids: list[str], session_key: str
) -> ConfirmedOwnedSpiritList:
    """构建用户确认拥有的精灵列表。

    Args:
        spirit_ids: 已确认的精灵 ID 列表
        session_key: 会话键 "user_id:chat_id"

    Returns:
        ConfirmedOwnedSpiritList 对象
    """
    from datetime import datetime, timezone

    return ConfirmedOwnedSpiritList(
        spirit_ids=spirit_ids,
        confirmed_at=datetime.now(timezone.utc).isoformat(),
        session_key=session_key,
    )
