"""
BWIKI 端点构造器 — 构造 MediaWiki API 请求 URL 和 wiki 页面链接。

对齐: data-layer-system.md §5.1 build_wiki_link(spirit_name)
"""

from __future__ import annotations

from urllib.parse import quote

BWIKI_BASE_URL = "https://wiki.biligame.com/rocom"
BWIKI_API_URL = f"{BWIKI_BASE_URL}/api.php"


def build_wiki_link(spirit_name: str) -> str:
    """构造精灵的 BWIKI 页面链接。"""
    encoded = quote(spirit_name, safe="")
    return f"{BWIKI_BASE_URL}/{encoded}"


def build_parse_api_params(page_title: str) -> dict[str, str]:
    """构造 MediaWiki action=parse API 请求参数。"""
    return {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
        "utf8": "1",
    }
