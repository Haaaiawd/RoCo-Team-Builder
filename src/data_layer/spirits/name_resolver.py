"""
名称解析器 — 精灵名称规范化、别名解析与模糊候选排序。

解析优先级: 规范名精确 > 别名精确 > 模糊匹配 (rapidfuzz)
对齐: data-layer-system.md §5.1 resolve_spirit_name(query)
     data-layer-system.detail.md §3.1 伪代码、§4 决策树
"""

from __future__ import annotations

import unicodedata

from ..app.contracts import SearchCandidate
from ..app.errors import AmbiguousSpiritNameError, SpiritNotFoundError
from .alias_index import AliasIndex
from .fuzzy_matcher import fuzzy_match

ALIAS_EXACT_PRIORITY: float = 100.0
CANONICAL_EXACT_PRIORITY: float = 120.0
HIGH_CONFIDENCE_THRESHOLD: float = 90.0


def normalize_text(text: str) -> str:
    """输入清洗 — 去除首尾空白、NFKC 规范化、转小写。"""
    cleaned = text.strip()
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = cleaned.lower()
    return cleaned


class NameResolver:
    """精灵名称解析器。

    依赖 AliasIndex 提供规范名与别名表，
    依赖 fuzzy_match 提供模糊候选。
    """

    def __init__(self, alias_index: AliasIndex) -> None:
        self._alias_index = alias_index

    def resolve(self, query: str) -> dict:
        """解析精灵名称。

        Returns:
            {
                "status": "resolved",
                "canonical_name": str,
                "candidates": list[SearchCandidate],
            }

        Raises:
            SpiritNotFoundError: 完全未命中
            AmbiguousSpiritNameError: 多个候选分数接近
        """
        cleaned = normalize_text(query)
        if not cleaned:
            raise SpiritNotFoundError(
                "输入为空，无法解析精灵名称",
            )

        canonical_hit = self._alias_index.lookup_canonical(cleaned)
        if canonical_hit is not None:
            return {
                "status": "resolved",
                "canonical_name": canonical_hit,
                "candidates": [
                    SearchCandidate(
                        canonical_name=canonical_hit,
                        display_name=canonical_hit,
                        score=CANONICAL_EXACT_PRIORITY,
                        match_reason="canonical",
                    )
                ],
            }

        alias_hit = self._alias_index.lookup_alias(cleaned)
        if alias_hit is not None:
            return {
                "status": "resolved",
                "canonical_name": alias_hit,
                "candidates": [
                    SearchCandidate(
                        canonical_name=alias_hit,
                        display_name=alias_hit,
                        score=ALIAS_EXACT_PRIORITY,
                        match_reason="alias",
                    )
                ],
            }

        fuzzy_candidates = fuzzy_match(
            cleaned,
            self._alias_index.canonical_names,
        )

        if not fuzzy_candidates:
            raise SpiritNotFoundError(
                f"未找到与 '{query}' 匹配的精灵",
            )

        if len(fuzzy_candidates) == 1 and fuzzy_candidates[0].score >= HIGH_CONFIDENCE_THRESHOLD:
            return {
                "status": "resolved",
                "canonical_name": fuzzy_candidates[0].canonical_name,
                "candidates": fuzzy_candidates,
            }

        raise AmbiguousSpiritNameError(
            f"精灵名称 '{query}' 存在多个候选，请确认",
            candidates=fuzzy_candidates,
        )
