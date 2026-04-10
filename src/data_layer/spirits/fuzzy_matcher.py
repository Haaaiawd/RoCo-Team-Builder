"""
模糊匹配器 — 基于 rapidfuzz 的精灵名称相似度搜索。

对齐: data-layer-system.md §4.2 Fuzzy Matcher、§7 技术选型 (rapidfuzz)
     data-layer-system.detail.md §1 配置常量 (FUZZY_MATCH_LIMIT, FUZZY_MATCH_MIN_SCORE)
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

from ..app.contracts import SearchCandidate

FUZZY_MATCH_LIMIT: int = 5
FUZZY_MATCH_MIN_SCORE: float = 70.0


def fuzzy_match(
    query: str,
    canonical_names: list[str],
    *,
    limit: int = FUZZY_MATCH_LIMIT,
    min_score: float = FUZZY_MATCH_MIN_SCORE,
) -> list[SearchCandidate]:
    """对查询词在规范名列表中进行模糊匹配，返回按分数降序的候选列表。

    使用 token_sort_ratio 以容忍词序变化。
    仅返回 score >= min_score 的候选。
    """
    if not query or not canonical_names:
        return []

    results = process.extract(
        query,
        canonical_names,
        scorer=fuzz.token_sort_ratio,
        limit=limit,
    )

    candidates: list[SearchCandidate] = []
    for match_name, score, _index in results:
        if score < min_score:
            continue
        candidates.append(
            SearchCandidate(
                canonical_name=match_name,
                display_name=match_name,
                score=score,
                match_reason="fuzzy",
            )
        )

    return candidates
