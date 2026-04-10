"""
属性克制矩阵 — 读取 type_chart.json 提供属性克制查询。

对齐: data-layer-system.md §4.2 Type Matchup Store
     data-layer-system.detail.md §1 ALLOWED_STATIC_TOPICS

不依赖网络，纯本地计算。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..app.contracts import TypeMatchupResult
from ..app.errors import InvalidTypeComboError

_DATA_DIR = Path(__file__).parent / "data"
_TYPE_CHART_PATH = _DATA_DIR / "type_chart.json"


class TypeMatchupStore:
    """属性克制矩阵查询器。

    启动时一次性加载 type_chart.json，后续查询为纯内存计算。
    """

    def __init__(self, chart_path: Path | None = None) -> None:
        path = chart_path or _TYPE_CHART_PATH
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        self._types: list[str] = data["types"]
        self._types_set: set[str] = set(self._types)
        self._matchups: dict[str, dict[str, Any]] = data["matchups"]

    @property
    def valid_types(self) -> set[str]:
        return self._types_set

    def get_type_matchup(self, type_combo: list[str]) -> TypeMatchupResult:
        """计算 1-2 个属性的克制关系。

        Args:
            type_combo: 1-2 个属性名列表

        Returns:
            TypeMatchupResult 包含进攻优势、防御弱点和防御抗性

        Raises:
            InvalidTypeComboError: 属性数量不合法或属性名不在白名单中
        """
        if not type_combo or len(type_combo) > 2:
            raise InvalidTypeComboError(
                f"属性组合需要 1-2 个属性，收到 {len(type_combo)} 个"
            )

        for t in type_combo:
            if t not in self._types_set:
                raise InvalidTypeComboError(
                    f"未知属性类型: '{t}'，合法属性: {sorted(self._types_set)}"
                )

        attack_advantages: list[dict] = []
        defense_weaknesses: list[dict] = []
        defense_resistances: list[dict] = []

        seen_attack: set[str] = set()
        for t in type_combo:
            entry = self._matchups.get(t, {})
            for target in entry.get("super_effective_against", []):
                if target not in seen_attack:
                    seen_attack.add(target)
                    attack_advantages.append(
                        {"target_type": target, "multiplier": 2.0, "source_type": t}
                    )

        weak_counts: dict[str, list[str]] = {}
        resist_counts: dict[str, list[str]] = {}

        for t in type_combo:
            entry = self._matchups.get(t, {})
            for source in entry.get("weak_to", []):
                weak_counts.setdefault(source, []).append(t)
            for source in entry.get("not_very_effective_from", []):
                resist_counts.setdefault(source, []).append(t)

        for source, from_types in weak_counts.items():
            if source not in resist_counts:
                multiplier = 2.0 ** len(from_types)
                defense_weaknesses.append(
                    {"source_type": source, "multiplier": multiplier}
                )

        for source, from_types in resist_counts.items():
            if source not in weak_counts:
                multiplier = 0.5 ** len(from_types)
                defense_resistances.append(
                    {"source_type": source, "multiplier": multiplier}
                )

        return TypeMatchupResult(
            input_types=list(type_combo),
            attack_advantages=attack_advantages,
            defense_weaknesses=defense_weaknesses,
            defense_resistances=defense_resistances,
        )
