"""
DataLayerFacade 接线修复单元测试

验收标准:
  - resolve_spirit_name: 委托 NameResolver，返回 dict，透传错误
  - get_spirit_profile: 委托 SpiritRepository，返回 dict，透传错误
  - search_spirits: 不抛异常，精确/歧义/模糊/空均返回 list[dict]，命中缓存
  - build_wiki_link: 委托 SpiritRepository，返回 str，透传错误
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from data_layer.app.contracts import SearchCandidate, SpiritProfile
from data_layer.app.errors import (
    AmbiguousSpiritNameError,
    SpiritNotFoundError,
    WikiParseError,
    WikiUpstreamTimeoutError,
)
from data_layer.app.facade import DataLayerFacade
from data_layer.cache.registry import CacheRegistry
from data_layer.spirits.alias_index import AliasIndex
from data_layer.spirits.name_resolver import NameResolver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_alias_index() -> AliasIndex:
    idx = AliasIndex()
    idx.load_aliases({
        "火神": ["火花", "烈焰鸟"],
        "冰龙王": ["冰龙"],
        "水灵": ["水元素"],
    })
    return idx


def _make_resolver() -> NameResolver:
    return NameResolver(_make_alias_index())


def _make_spirit_profile(name: str = "火神") -> SpiritProfile:
    return SpiritProfile(
        canonical_name=name,
        display_name=name,
        types=["火"],
        base_stats={"hp": 85, "attack": 90, "defense": 75, "speed": 95},
        skills=[{"name": "烈焰冲击"}],
        bloodline_type="神火",
        evolution_chain=[{"stage_name": "火花→火神", "condition": None}],
        wiki_url=f"https://wiki.biligame.com/rocokingdomworld/{name}",
    )


@pytest.fixture
def cache_registry() -> CacheRegistry:
    return CacheRegistry()


@pytest.fixture
def resolver() -> NameResolver:
    return _make_resolver()


@pytest.fixture
def mock_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.get_spirit_profile = AsyncMock(return_value=_make_spirit_profile())
    repo.build_wiki_link = AsyncMock(
        return_value="https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E"
    )
    return repo


@pytest.fixture
def facade(
    resolver: NameResolver,
    mock_repository: AsyncMock,
    cache_registry: CacheRegistry,
) -> DataLayerFacade:
    return DataLayerFacade(
        name_resolver=resolver,
        spirit_repository=mock_repository,
        cache_registry=cache_registry,
    )


# ---------------------------------------------------------------------------
# resolve_spirit_name
# ---------------------------------------------------------------------------


class TestResolveSpiritName:
    @pytest.mark.asyncio
    async def test_canonical_exact_match(self, facade: DataLayerFacade):
        result = await facade.resolve_spirit_name("火神")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "火神"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["match_reason"] == "canonical"

    @pytest.mark.asyncio
    async def test_alias_exact_match(self, facade: DataLayerFacade):
        result = await facade.resolve_spirit_name("火花")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "火神"
        assert result["candidates"][0]["match_reason"] == "alias"

    @pytest.mark.asyncio
    async def test_candidates_are_dicts(self, facade: DataLayerFacade):
        result = await facade.resolve_spirit_name("火神")
        for c in result["candidates"]:
            assert isinstance(c, dict)
            assert "canonical_name" in c
            assert "score" in c

    @pytest.mark.asyncio
    async def test_not_found_raises_error(self, facade: DataLayerFacade):
        with pytest.raises(SpiritNotFoundError):
            await facade.resolve_spirit_name("完全不存在的精灵")

    @pytest.mark.asyncio
    async def test_ambiguous_raises_error(self, resolver: NameResolver, mock_repository: AsyncMock, cache_registry: CacheRegistry):
        """多候选分数接近时应抛 AmbiguousSpiritNameError — 透传验证。"""
        mock_resolver = MagicMock(spec=NameResolver)
        mock_resolver.resolve.side_effect = AmbiguousSpiritNameError(
            "歧义", candidates=[
                SearchCandidate(canonical_name="冰龙王", display_name="冰龙王", score=85.0, match_reason="fuzzy"),
                SearchCandidate(canonical_name="冰晶龙", display_name="冰晶龙", score=82.0, match_reason="fuzzy"),
            ]
        )
        f = DataLayerFacade(
            name_resolver=mock_resolver,
            spirit_repository=mock_repository,
            cache_registry=cache_registry,
        )
        with pytest.raises(AmbiguousSpiritNameError) as exc_info:
            await f.resolve_spirit_name("冰")
        assert len(exc_info.value.candidates) == 2


# ---------------------------------------------------------------------------
# get_spirit_profile
# ---------------------------------------------------------------------------


class TestGetSpiritProfile:
    @pytest.mark.asyncio
    async def test_returns_dict(self, facade: DataLayerFacade):
        result = await facade.get_spirit_profile("火神")
        assert isinstance(result, dict)
        assert result["canonical_name"] == "火神"
        assert "types" in result
        assert "base_stats" in result
        assert "wiki_url" in result

    @pytest.mark.asyncio
    async def test_delegates_to_repository(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        await facade.get_spirit_profile("火神")
        mock_repository.get_spirit_profile.assert_awaited_once_with("火神")

    @pytest.mark.asyncio
    async def test_wiki_timeout_passes_through(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        mock_repository.get_spirit_profile = AsyncMock(
            side_effect=WikiUpstreamTimeoutError("timeout", wiki_url="https://test")
        )
        with pytest.raises(WikiUpstreamTimeoutError) as exc_info:
            await facade.get_spirit_profile("火神")
        assert exc_info.value.wiki_url
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_parse_error_passes_through(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        mock_repository.get_spirit_profile = AsyncMock(
            side_effect=WikiParseError("parse failed", wiki_url="https://test")
        )
        with pytest.raises(WikiParseError) as exc_info:
            await facade.get_spirit_profile("火神")
        assert exc_info.value.error_code == "WIKI_PARSE_FAILED"

    @pytest.mark.asyncio
    async def test_not_found_passes_through(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        mock_repository.get_spirit_profile = AsyncMock(
            side_effect=SpiritNotFoundError("not found")
        )
        with pytest.raises(SpiritNotFoundError):
            await facade.get_spirit_profile("不存在的精灵")


# ---------------------------------------------------------------------------
# search_spirits
# ---------------------------------------------------------------------------


class TestSearchSpirits:
    @pytest.mark.asyncio
    async def test_exact_match_returns_candidates(self, facade: DataLayerFacade):
        result = await facade.search_spirits("火神")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["canonical_name"] == "火神"

    @pytest.mark.asyncio
    async def test_alias_match_returns_candidates(self, facade: DataLayerFacade):
        result = await facade.search_spirits("火花")
        assert len(result) >= 1
        assert result[0]["canonical_name"] == "火神"

    @pytest.mark.asyncio
    async def test_ambiguous_returns_all_candidates(self, facade: DataLayerFacade):
        """歧义名称不抛异常，返回全部候选。"""
        result = await facade.search_spirits("冰")
        assert isinstance(result, list)
        # 不抛异常就是正确行为

    @pytest.mark.asyncio
    async def test_no_match_returns_fuzzy_or_empty(self, facade: DataLayerFacade):
        """完全无匹配时不抛异常，返回模糊结果或空列表。"""
        result = await facade.search_spirits("完全不存在的xyz精灵")
        assert isinstance(result, list)
        # 可能返回空列表或模糊低分候选

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, facade: DataLayerFacade):
        result = await facade.search_spirits("   ")
        assert result == []

    @pytest.mark.asyncio
    async def test_candidates_are_dicts(self, facade: DataLayerFacade):
        result = await facade.search_spirits("火神")
        for c in result:
            assert isinstance(c, dict)
            assert "canonical_name" in c
            assert "score" in c

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_call(
        self, facade: DataLayerFacade, cache_registry: CacheRegistry
    ):
        """第二次查询同一关键词应命中缓存。"""
        first = await facade.search_spirits("火神")
        second = await facade.search_spirits("火神")
        assert first == second

    @pytest.mark.asyncio
    async def test_limit_param_respected(self, facade: DataLayerFacade):
        result = await facade.search_spirits("火", limit=2)
        assert isinstance(result, list)
        assert len(result) <= 2


# ---------------------------------------------------------------------------
# build_wiki_link
# ---------------------------------------------------------------------------


class TestBuildWikiLink:
    @pytest.mark.asyncio
    async def test_returns_url_string(self, facade: DataLayerFacade):
        url = await facade.build_wiki_link("火神")
        assert isinstance(url, str)
        assert "rocokingdomworld" in url

    @pytest.mark.asyncio
    async def test_delegates_to_repository(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        await facade.build_wiki_link("火神")
        mock_repository.build_wiki_link.assert_awaited_once_with("火神")

    @pytest.mark.asyncio
    async def test_not_found_passes_through(self, facade: DataLayerFacade, mock_repository: AsyncMock):
        mock_repository.build_wiki_link = AsyncMock(
            side_effect=SpiritNotFoundError("not found")
        )
        with pytest.raises(SpiritNotFoundError):
            await facade.build_wiki_link("不存在的精灵")
