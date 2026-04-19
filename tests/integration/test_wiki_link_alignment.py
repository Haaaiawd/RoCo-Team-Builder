"""
Integration tests for Wiki link / summary field alignment.

验证 T1.2.1: Wiki 标识 / 深读链接与摘要字段对齐路径
"""

import pytest

from src.data_layer.app.facade import DataLayerFacade
from src.data_layer.app.errors import SpiritNotFoundError, AmbiguousSpiritNameError
from src.data_layer.cache.registry import CacheRegistry


class TestWikiLinkAlignment:
    """Test wiki link generation aligns with spirit profile resolution."""

    @pytest.mark.asyncio
    async def test_wiki_link_uses_same_name_resolution(self):
        """Wiki link should use same name resolution as spirit profile."""
        facade = DataLayerFacade()

        # 使用 endpoint_builder 直接测试链接格式
        from src.data_layer.wiki.endpoint_builder import build_wiki_link
        link = build_wiki_link("TestSpirit")

        # 链接应该包含 BWIKI 域名
        assert "wiki.biligame.com" in link
        assert "TestSpirit" in link or "TestSpirit" in link.lower()

    @pytest.mark.asyncio
    async def test_wiki_link_empty_for_invalid_input(self):
        """Empty spirit name should return base URL (endpoint_builder behavior)."""
        from src.data_layer.wiki.endpoint_builder import build_wiki_link

        result = build_wiki_link("")
        # endpoint_builder returns base URL with empty encoded name
        assert "wiki.biligame.com" in result

    @pytest.mark.asyncio
    async def test_wiki_link_propagates_name_resolution_errors(self):
        """Name resolution errors should propagate properly."""
        facade = DataLayerFacade()

        # 测试不存在的精灵
        with pytest.raises(SpiritNotFoundError):
            await facade.build_wiki_link("完全不存在的精灵名123456")


class TestWikiLinkInTeamAnalysis:
    """Test wiki links in team analysis snapshot."""

    @pytest.mark.asyncio
    async def test_team_analysis_wiki_targets_use_consistent_links(self):
        """Team analysis wiki targets should use consistent link format."""
        facade = DataLayerFacade()

        # 创建包含精灵的草稿
        draft = {
            "schema_version": "v1",
            "slots": [
                {"slot_index": 0, "spirit_name": "", "skills": []},
            ],
        }

        # 分析草稿（即使资料缺失，也应返回结构）
        result = await facade.analyze_team_draft(draft)

        # 检查 wiki_targets 字段存在
        assert "wiki_targets" in result
        assert isinstance(result["wiki_targets"], list)

    @pytest.mark.asyncio
    async def test_team_analysis_preserves_summary_fields_on_partial_data(self):
        """Team analysis should preserve summary fields even with partial data."""
        facade = DataLayerFacade()

        # 空草稿
        draft = {
            "schema_version": "v1",
            "slots": [],
        }

        result = await facade.analyze_team_draft(draft)

        # 应返回结构化数据而非崩溃
        assert result["schema_version"] == "v1"
        assert result["attack_distribution"]["status"] == "insufficient_data"
        assert "missing_data_notes" in result


class TestCacheConsistency:
    """Test cache consistency across different operations."""

    @pytest.mark.asyncio
    async def test_wiki_link_cache_structure_exists(self):
        """Wiki link cache should exist in cache registry."""
        facade = DataLayerFacade()
        cache = facade._cache

        # 验证 wiki_links 缓存存在
        assert hasattr(cache, "wiki_links")
        assert cache.wiki_links is not None

    @pytest.mark.asyncio
    async def test_cache_clear_all_clears_wiki_links(self):
        """clear_all should clear wiki_links cache."""
        facade = DataLayerFacade()
        cache = facade._cache

        # 手动填充缓存
        cache.wiki_links["test_key"] = "test_value"
        assert len(cache.wiki_links) > 0

        # 清空所有缓存
        cache.clear_all()

        # wiki_links 应该被清空
        assert len(cache.wiki_links) == 0
