"""
Wiki Link Resolver — 生成与摘要展示一致的 wiki 标识 / 深读链接。

保证站内摘要与外链目标一致。
对齐: data-layer-system.md §4.2 Wiki Link Resolver
"""

from __future__ import annotations

from typing import Any


def build_wiki_link(spirit_name: str) -> str:
    """构造 BWIKI 页面链接。

    Args:
        spirit_name: 精灵规范名

    Returns:
        BWIKI 页面 URL
    """
    if not spirit_name:
        return ""

    # BWIKI URL 格式: https://wiki.biligame.com/rocokingdomworld/{精灵名}
    # 使用 URL 编码处理特殊字符
    from urllib.parse import quote

    encoded_name = quote(spirit_name)
    return f"https://wiki.biligame.com/rocokingdomworld/{encoded_name}"


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
