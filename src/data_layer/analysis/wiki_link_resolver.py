"""
Wiki Link Resolver — 生成与摘要展示一致的 wiki 标识 / 深读链接。

保证站内摘要与外链目标一致。
对齐: data-layer-system.md §4.2 Wiki Link Resolver
"""

from __future__ import annotations

from typing import Any

from ..wiki.endpoint_builder import build_wiki_link as _build_wiki_link


def build_wiki_link(spirit_name: str) -> str:
    """构造 BWIKI 页面链接（统一使用 endpoint_builder）。

    Args:
        spirit_name: 精灵规范名

    Returns:
        BWIKI 页面 URL，空字符串表示无效输入
    """
    if not spirit_name:
        return ""

    return _build_wiki_link(spirit_name)


def build_wiki_targets(spirit_profiles: list[dict]) -> list[dict]:
    """为精灵列表构建 wiki 目标列表。

    Args:
        spirit_profiles: 精灵资料列表

    Returns:
        wiki 目标列表，每个包含 canonical_name 和 wiki_url
    """
    targets = []
    for profile in spirit_profiles:
        if not isinstance(profile, dict):
            continue

        canonical_name = profile.get("canonical_name") or profile.get("display_name")
        if not canonical_name:
            continue

        wiki_url = profile.get("wiki_url") or build_wiki_link(canonical_name)

        targets.append({
            "canonical_name": canonical_name,
            "wiki_url": wiki_url,
        })

    return targets
