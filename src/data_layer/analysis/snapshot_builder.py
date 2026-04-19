"""
Team Analysis Snapshot Builder — 核心分析计算引擎。

实现五类结构化分析区块的计算逻辑。
对齐: data-layer-system.detail.md §3.6 analyze_team_draft()
"""

from __future__ import annotations

import uuid
from collections import Counter
from typing import Any

from ..app.contracts import TeamAnalysisSection, TeamAnalysisSnapshot
from ..app.errors import TeamAnalysisDataGapError
from .draft_normalizer import build_team_fingerprint
from .wiki_link_resolver import build_wiki_targets


# 分析区块键名常量
SECTION_KEYS = {
    "attack_distribution": "attack_distribution",
    "attack_coverage": "attack_coverage",
    "defense_focus": "defense_focus",
    "resistance_highlights": "resistance_highlights",
    "pressure_points": "pressure_points",
}

# 分析区块标题常量
SECTION_TITLES = {
    "attack_distribution": "攻向分布",
    "attack_coverage": "攻击覆盖",
    "defense_focus": "防守侧重点",
    "resistance_highlights": "抗性较多",
    "pressure_points": "易被压制",
}


def build_attack_distribution_section(
    profiles: list[dict], status: str
) -> TeamAnalysisSection:
    """构建攻向分布区块。

    统计队伍中所有精灵的属性分布。
    """
    type_counter = Counter()

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        types = profile.get("types", [])
        if isinstance(types, list):
            for t in types:
                if t:
                    type_counter[t] += 1

    items = [
        {"type": t, "count": count}
        for t, count in type_counter.most_common()
    ]

    notes = []
    if status == "insufficient_data":
        notes.append("队伍为空，无法计算攻向分布")
    elif status == "partial_unavailable":
        notes.append("部分精灵资料缺失，基于可用数据计算")

    return TeamAnalysisSection(
        key=SECTION_KEYS["attack_distribution"],
        title=SECTION_TITLES["attack_distribution"],
        items=items,
        status=status,
        notes=notes,
    )


def build_attack_coverage_section(
    profiles: list[dict], status: str
) -> TeamAnalysisSection:
    """构建攻击覆盖区块。

    基于队伍属性组合计算对不同属性的优势覆盖。
    """
    # 收集队伍中所有属性
    all_types = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        types = profile.get("types", [])
        if isinstance(types, list):
            all_types.update(types)

    # 简化版：直接列出队伍拥有的属性
    # 完整版应基于属性克制表计算优势覆盖
    items = [
        {"type": t, "has_coverage": True}
        for t in sorted(all_types)
    ]

    notes = []
    if status == "insufficient_data":
        notes.append("队伍为空，无法计算攻击覆盖")
    elif status == "partial_unavailable":
        notes.append("部分精灵资料缺失，基于可用数据计算")

    return TeamAnalysisSection(
        key=SECTION_KEYS["attack_coverage"],
        title=SECTION_TITLES["attack_coverage"],
        items=items,
        status=status,
        notes=notes,
    )


def build_defense_focus_section(
    profiles: list[dict], status: str
) -> TeamAnalysisSection:
    """构建防守侧重点区块。

    基于种族值分布判断队伍的防守倾向（血量、防御、魔抗等）。
    """
    total_stats = {
        "hp": 0,
        "attack": 0,
        "defense": 0,
        "magic_attack": 0,
        "magic_defense": 0,
        "speed": 0,
    }
    count = 0

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        base_stats = profile.get("base_stats", {})
        if isinstance(base_stats, dict):
            for stat in total_stats:
                total_stats[stat] += base_stats.get(stat, 0)
            count += 1

    items = []
    if count > 0:
        # 找出最高的防守相关属性
        defense_avg = total_stats["defense"] / count
        magic_defense_avg = total_stats["magic_defense"] / count
        hp_avg = total_stats["hp"] / count

        if defense_avg > magic_defense_avg and defense_avg > hp_avg:
            items.append({"focus": "物理防御", "reason": "平均物防最高"})
        elif magic_defense_avg > defense_avg and magic_defense_avg > hp_avg:
            items.append({"focus": "魔法防御", "reason": "平均魔抗最高"})
        elif hp_avg > defense_avg and hp_avg > magic_defense_avg:
            items.append({"focus": "血量耐久", "reason": "平均血量最高"})
        else:
            items.append({"focus": "均衡防守", "reason": "防守属性较为均衡"})
    else:
        items.append({"focus": "无数据", "reason": "队伍为空"})

    notes = []
    if status == "insufficient_data":
        notes.append("队伍为空，无法判断防守侧重点")
    elif status == "partial_unavailable":
        notes.append("部分精灵资料缺失，基于可用数据计算")

    return TeamAnalysisSection(
        key=SECTION_KEYS["defense_focus"],
        title=SECTION_TITLES["defense_focus"],
        items=items,
        status=status,
        notes=notes,
    )


def build_resistance_highlights_section(
    profiles: list[dict], status: str
) -> TeamAnalysisSection:
    """构建抗性较多区块。

    列出队伍整体抗性较好的属性。
    """
    # 简化版：基于精灵属性推断抗性倾向
    # 完整版应基于属性克制表计算实际抗性
    type_counter = Counter()

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        types = profile.get("types", [])
        if isinstance(types, list):
            for t in types:
                if t:
                    type_counter[t] += 1

    items = [
        {"type": t, "count": count, "note": "基于队伍属性推断"}
        for t, count in type_counter.most_common()
    ]

    notes = []
    if status == "insufficient_data":
        notes.append("队伍为空，无法分析抗性")
    elif status == "partial_unavailable":
        notes.append("部分精灵资料缺失，基于可用数据计算")

    return TeamAnalysisSection(
        key=SECTION_KEYS["resistance_highlights"],
        title=SECTION_TITLES["resistance_highlights"],
        items=items,
        status=status,
        notes=notes,
    )


def build_pressure_points_section(
    profiles: list[dict], status: str
) -> TeamAnalysisSection:
    """构建易被压制区块。

    列出队伍整体较弱的属性或被克制的类型。
    """
    # 简化版：基于属性分布推断可能的弱点
    # 完整版应基于属性克制表计算实际弱点
    type_counter = Counter()

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        types = profile.get("types", [])
        if isinstance(types, list):
            for t in types:
                if t:
                    type_counter[t] += 1

    # 简化逻辑：属性单一可能被克制
    items = []
    if len(type_counter) == 1:
        dominant_type = list(type_counter.keys())[0]
        items.append({
            "type": dominant_type,
            "risk": "属性单一",
            "note": "队伍属性较为单一，可能被特定属性克制"
        })
    else:
        items.append({"risk": "属性均衡", "note": "队伍属性分布较为均衡"})

    notes = []
    if status == "insufficient_data":
        notes.append("队伍为空，无法分析弱点")
    elif status == "partial_unavailable":
        notes.append("部分精灵资料缺失，基于可用数据计算")

    return TeamAnalysisSection(
        key=SECTION_KEYS["pressure_points"],
        title=SECTION_TITLES["pressure_points"],
        items=items,
        status=status,
        notes=notes,
    )


def build_missing_data_notes(missing_slots: list[int]) -> list[str]:
    """构建数据缺失说明。

    Args:
        missing_slots: 缺失资料的槽位索引列表

    Returns:
        缺失说明列表
    """
    if not missing_slots:
        return []

    if len(missing_slots) == 1:
        return [f"槽位 {missing_slots[0]} 精灵资料缺失"]
    elif len(missing_slots) <= 3:
        return [f"槽位 {', '.join(map(str, missing_slots))} 精灵资料缺失"]
    else:
        return [f"槽位 {', '.join(map(str, missing_slots[:3]))} 等 {len(missing_slots)} 个槽位精灵资料缺失"]


def analyze_team_draft(
    normalized_draft: dict,
    spirit_profiles: list[dict],
    missing_slots: list[int],
) -> TeamAnalysisSnapshot:
    """分析队伍草稿，返回 TeamAnalysisSnapshot。

    Args:
        normalized_draft: 归一化后的 TeamDraft
        spirit_profiles: 成功获取的精灵资料列表
        missing_slots: 资料缺失的槽位索引列表

    Returns:
        TeamAnalysisSnapshot 实例

    Raises:
        TeamAnalysisDataGapError: 当数据严重不足时
    """
    slots = normalized_draft.get("slots", [])

    # 确定整体状态
    if not slots:
        status = "insufficient_data"
    elif len(missing_slots) == len(slots):
        # 检查是否所有槽位都有 spirit_name 但资料获取失败
        has_spirit_names = any(slot.get("spirit_name") for slot in slots)
        if has_spirit_names:
            # 有精灵名但资料全部缺失，这是数据缺口错误
            raise TeamAnalysisDataGapError(
                "队伍草稿存在但所有精灵资料均缺失",
                missing_sections=["all"],
            )
        status = "insufficient_data"
    elif missing_slots:
        status = "partial_unavailable"
    else:
        status = "ready"

    # 构建指纹
    team_fingerprint = build_team_fingerprint(slots)

    # 构建五个分析区块
    attack_distribution = build_attack_distribution_section(spirit_profiles, status)
    attack_coverage = build_attack_coverage_section(spirit_profiles, status)
    defense_focus = build_defense_focus_section(spirit_profiles, status)
    resistance_highlights = build_resistance_highlights_section(spirit_profiles, status)
    pressure_points = build_pressure_points_section(spirit_profiles, status)

    # 构建 wiki 目标
    wiki_targets = build_wiki_targets(spirit_profiles)

    # 构建缺失说明
    missing_data_notes = build_missing_data_notes(missing_slots)

    return TeamAnalysisSnapshot(
        schema_version="v1",
        request_id=str(uuid.uuid4()),
        team_fingerprint=team_fingerprint,
        attack_distribution=attack_distribution,
        attack_coverage=attack_coverage,
        defense_focus=defense_focus,
        resistance_highlights=resistance_highlights,
        pressure_points=pressure_points,
        wiki_targets=wiki_targets,
        missing_data_notes=missing_data_notes,
    )
