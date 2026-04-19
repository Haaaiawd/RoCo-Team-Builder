"""
静态机制知识库 — 提供配队推理所需的非网络依赖知识查询。

对齐: data-layer-system.md §4.2 Static Knowledge Store
     data-layer-system.detail.md §1 ALLOWED_STATIC_TOPICS

支持的 topic_key:
  - type_chart: 属性克制机制说明
  - nature_chart: 性格加成机制说明
  - bloodline_rules: 血脉系统规则 (预留)
  - battle_mechanics: 战斗基础机制 (预留)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..app.contracts import StaticKnowledgeEntry
from ..app.errors import KnowledgeTopicNotFoundError

_DATA_DIR = Path(__file__).parent / "data"

ALLOWED_TOPICS: set[str] = {
    "type_chart",
    "nature_chart",
    "bloodline_rules",
    "battle_mechanics",
}


class StaticKnowledgeStore:
    """静态机制知识查询器。

    启动时加载所有已有的 JSON 数据文件。
    对尚未填充的 topic 返回占位说明。
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or _DATA_DIR
        self._cache: dict[str, StaticKnowledgeEntry] = {}
        self._load_all()

    def _load_all(self) -> None:
        """加载所有可用的静态知识文件。"""
        self._load_type_chart()
        self._load_nature_chart()
        self._register_placeholder("bloodline_rules", "血脉系统规则", "血脉系统规则尚未收录，后续版本将补充。")
        self._register_placeholder("battle_mechanics", "战斗基础机制", "战斗基础机制知识尚未收录，后续版本将补充。")

    def _load_type_chart(self) -> None:
        path = self._data_dir / "type_chart.json"
        if not path.exists():
            self._register_placeholder("type_chart", "属性克制表", "属性克制数据文件缺失。")
            return

        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        meta = data.get("_meta", {})
        types = data.get("types", [])
        matchups = data.get("matchups", {})

        summary_lines = [f"洛克王国：世界共有 {len(types)} 种属性: {', '.join(types)}。"]
        summary_lines.append("")
        for t in types:
            entry = matchups.get(t, {})
            se = entry.get("super_effective_against", [])
            wt = entry.get("weak_to", [])
            if se or wt:
                parts = []
                if se:
                    parts.append(f"克制 {'/'.join(se)}")
                if wt:
                    parts.append(f"弱于 {'/'.join(wt)}")
                summary_lines.append(f"  {t}: {'; '.join(parts)}")

        self._cache["type_chart"] = StaticKnowledgeEntry(
            topic_key="type_chart",
            title="属性克制表",
            content="\n".join(summary_lines),
            source=meta.get("source", "本地静态文件"),
        )

    def _load_nature_chart(self) -> None:
        path = self._data_dir / "nature_chart.json"
        if not path.exists():
            self._register_placeholder("nature_chart", "宠物性格加成表", "性格加成数据文件缺失。")
            return

        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        meta = data.get("_meta", {})
        natures = data.get("natures", {})

        summary_lines = [f"洛克王国：世界共有 {len(natures)} 种性格。"]
        summary_lines.append("每种性格 +10% 一项属性、-10% 另一项属性。")
        summary_lines.append("")

        by_category: dict[str, list[str]] = {}
        for name, info in natures.items():
            cat = info.get("category", "未知")
            boost = info.get("boost", "?")
            penalty = info.get("penalty", "?")
            desc = f"{name} (+{boost} -{penalty})"
            by_category.setdefault(cat, []).append(desc)

        for cat, items in by_category.items():
            summary_lines.append(f"  {cat}: {', '.join(items)}")

        self._cache["nature_chart"] = StaticKnowledgeEntry(
            topic_key="nature_chart",
            title="宠物性格加成表",
            content="\n".join(summary_lines),
            source=meta.get("source", "本地静态文件"),
        )

    def _register_placeholder(self, key: str, title: str, content: str) -> None:
        self._cache[key] = StaticKnowledgeEntry(
            topic_key=key,
            title=title,
            content=content,
            source="placeholder",
        )

    def get_static_knowledge(self, topic_key: str) -> StaticKnowledgeEntry:
        """查询指定 topic 的静态知识。

        Args:
            topic_key: 知识主题标识

        Returns:
            StaticKnowledgeEntry

        Raises:
            KnowledgeTopicNotFoundError: topic_key 不在允许集合中
        """
        if topic_key not in ALLOWED_TOPICS:
            raise KnowledgeTopicNotFoundError(
                f"未知知识主题: '{topic_key}'，支持的主题: {sorted(ALLOWED_TOPICS)}"
            )

        entry = self._cache.get(topic_key)
        if entry is None:
            raise KnowledgeTopicNotFoundError(
                f"知识主题 '{topic_key}' 尚未加载"
            )

        return entry
