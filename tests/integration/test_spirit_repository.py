"""
T1.2.1 集成测试 — 精灵仓储 + wiki 网关 + 解析器 + 缓存。

验收标准:
  - get_spirit_profile 返回包含种族值/系别/技能/血脉/进化链/wiki_url 的 SpiritProfile
  - 同一精灵在 TTL 窗口内重复查询命中缓存
  - BWIKI 超时时返回 WIKI_TIMEOUT_ 错误并携带 wiki_url
  - BWIKI 解析失败时返回 WIKI_PARSE_ 错误并携带 wiki_url
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from data_layer.app.contracts import SpiritProfile
from data_layer.app.errors import WikiParseError, WikiUpstreamTimeoutError
from data_layer.cache.registry import CacheRegistry
from data_layer.spirits.alias_index import AliasIndex
from data_layer.spirits.name_resolver import NameResolver
from data_layer.spirits.repository import SpiritRepository
from data_layer.wiki.gateway import WikiGateway
from data_layer.wiki.parser import WikiParser


# ---------------------------------------------------------------------------
# Mock data — 模拟 BWIKI MediaWiki API 的 action=parse 响应
# ---------------------------------------------------------------------------

MOCK_SPIRIT_RESPONSE: dict = {
    "parse": {
        "title": "火神",
        "pageid": 12345,
        "wikitext": {
            "*": (
                "{{精灵信息\n"
                "|系别=火\n"
                "|精力=85\n"
                "|攻击=90\n"
                "|防御=75\n"
                "|魔攻=120\n"
                "|魔抗=80\n"
                "|速度=95\n"
                "|血脉=神火\n"
                "|技能名1=烈焰冲击\n"
                "|技能名2=火焰旋涡\n"
                "|技能名3=灭世火焰\n"
                "|技能名4=凤凰涅槃\n"
                "|进化1=火花→火神\n"
                "}}"
            )
        },
    }
}

MOCK_EMPTY_RESPONSE: dict = {
    "parse": {
        "title": "不存在的页面",
        "wikitext": {"*": ""},
    }
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def alias_index() -> AliasIndex:
    idx = AliasIndex()
    idx.load_aliases({
        "火神": ["火花", "烈焰鸟"],
        "冰龙王": ["冰龙"],
    })
    return idx


@pytest.fixture
def cache_registry() -> CacheRegistry:
    return CacheRegistry()


@pytest.fixture
def wiki_parser() -> WikiParser:
    return WikiParser()


@pytest.fixture
def mock_gateway() -> WikiGateway:
    gw = WikiGateway()
    gw.fetch_spirit_page = AsyncMock(return_value=MOCK_SPIRIT_RESPONSE)
    return gw


@pytest.fixture
def repository(
    alias_index: AliasIndex,
    mock_gateway: WikiGateway,
    wiki_parser: WikiParser,
    cache_registry: CacheRegistry,
) -> SpiritRepository:
    resolver = NameResolver(alias_index)
    return SpiritRepository(resolver, mock_gateway, wiki_parser, cache_registry)


# ---------------------------------------------------------------------------
# Tests — get_spirit_profile 成功路径
# ---------------------------------------------------------------------------


class TestGetSpiritProfileSuccess:
    @pytest.mark.asyncio
    async def test_returns_spirit_profile(self, repository: SpiritRepository):
        """正常查询返回 SpiritProfile，包含全部必要字段。"""
        profile = await repository.get_spirit_profile("火神")
        assert isinstance(profile, SpiritProfile)
        assert profile.canonical_name == "火神"
        assert profile.display_name == "火神"
        assert "火" in profile.types
        assert profile.base_stats.get("hp") == 85
        assert profile.base_stats.get("attack") == 90
        assert profile.base_stats.get("speed") == 95
        assert len(profile.skills) >= 1
        assert profile.bloodline_type == "神火"
        assert profile.wiki_url
        assert "火神" in profile.wiki_url or "%E7%81%AB%E7%A5%9E" in profile.wiki_url

    @pytest.mark.asyncio
    async def test_alias_resolves_to_profile(self, repository: SpiritRepository):
        """通过别名查询也能正常返回。"""
        profile = await repository.get_spirit_profile("火花")
        assert profile.canonical_name == "火神"

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_call(
        self, repository: SpiritRepository, mock_gateway: WikiGateway
    ):
        """同一精灵第二次查询应命中缓存，不再访问 BWIKI。"""
        await repository.get_spirit_profile("火神")
        await repository.get_spirit_profile("火神")
        assert mock_gateway.fetch_spirit_page.call_count == 1


# ---------------------------------------------------------------------------
# Tests — get_spirit_profile 失败路径
# ---------------------------------------------------------------------------


class TestGetSpiritProfileFailure:
    @pytest.mark.asyncio
    async def test_timeout_returns_wiki_timeout_error(
        self, alias_index: AliasIndex, wiki_parser: WikiParser, cache_registry: CacheRegistry
    ):
        """BWIKI 超时时应抛 WikiUpstreamTimeoutError 且携带 wiki_url。"""
        gw = WikiGateway()
        gw.fetch_spirit_page = AsyncMock(
            side_effect=WikiUpstreamTimeoutError("timeout", wiki_url="https://test")
        )
        resolver = NameResolver(alias_index)
        repo = SpiritRepository(resolver, gw, wiki_parser, cache_registry)

        with pytest.raises(WikiUpstreamTimeoutError) as exc_info:
            await repo.get_spirit_profile("火神")
        assert exc_info.value.wiki_url
        assert exc_info.value.error_code == "WIKI_TIMEOUT_UPSTREAM"
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_parse_error_returns_wiki_parse_error(
        self, alias_index: AliasIndex, cache_registry: CacheRegistry
    ):
        """BWIKI 返回空内容时应抛 WikiParseError 且携带 wiki_url。"""
        gw = WikiGateway()
        gw.fetch_spirit_page = AsyncMock(return_value=MOCK_EMPTY_RESPONSE)
        parser = WikiParser()
        resolver = NameResolver(alias_index)
        repo = SpiritRepository(resolver, gw, parser, cache_registry)

        with pytest.raises(WikiParseError) as exc_info:
            await repo.get_spirit_profile("火神")
        assert exc_info.value.wiki_url
        assert exc_info.value.error_code == "WIKI_PARSE_FAILED"
        assert exc_info.value.retryable is False


# ---------------------------------------------------------------------------
# Tests — build_wiki_link
# ---------------------------------------------------------------------------


class TestBuildWikiLink:
    @pytest.mark.asyncio
    async def test_build_link_for_known_spirit(self, repository: SpiritRepository):
        url = await repository.build_wiki_link("火神")
        assert "rocom" in url
        assert "火神" in url or "%E7%81%AB%E7%A5%9E" in url

    @pytest.mark.asyncio
    async def test_build_link_via_alias(self, repository: SpiritRepository):
        url = await repository.build_wiki_link("火花")
        assert "rocom" in url
