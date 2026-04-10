"""
缓存键构造器 — 统一 cache key namespace。

对齐: data-layer-system.detail.md §1 CACHE_KEY_PREFIX
"""

from __future__ import annotations

CACHE_KEY_PREFIX = {
    "spirit_profile": "spirit_profile",
    "search_candidates": "search_candidates",
    "type_matchup": "type_matchup",
    "static_knowledge": "static_knowledge",
    "wiki_page_extract": "wiki_page_extract",
}


def build_cache_key(query_type: str, *parts: str) -> str:
    """构造缓存键。

    Args:
        query_type: CACHE_KEY_PREFIX 中的某个键
        parts: 组成缓存键的后缀部分（已规范化的名称等）

    Returns:
        格式: "{prefix}:{part1}:{part2}:..."
    """
    prefix = CACHE_KEY_PREFIX.get(query_type, query_type)
    suffix = ":".join(str(p).strip().lower() for p in parts)
    return f"{prefix}:{suffix}"
