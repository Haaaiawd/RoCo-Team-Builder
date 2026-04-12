"""
T3.2.2 集成测试 — 资料查询与卡片渲染工具集成。

验收标准:
  - Given 用户询问单只精灵资料 → When Agent 调用资料查询工具 → Then 返回结构化资料并附 BWIKI 链接
  - Given 精灵卡片渲染成功 → When 工具结果回传 → Then 输出 html/fallback_text/render_mode/metadata
  - Given BWIKI 超时或卡片渲染失败 → When 工具调用异常 → Then 仍返回带 wiki_url 的降级文本
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_backend.integrations.data_layer_client import DataLayerClient
from agent_backend.integrations.spirit_card_client import SpiritCardClient
from agent_backend.runtime.tool_registry import ToolRegistry
from data_layer.app.facade import DataLayerFacade
from data_layer.app.contracts import SpiritProfile
from spirit_card.app.facade import SpiritCardFacade


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def mock_data_facade() -> AsyncMock:
    facade = AsyncMock(spec=DataLayerFacade)
    facade.get_spirit_profile = AsyncMock(return_value=_make_spirit_profile())
    facade.search_spirits = AsyncMock(return_value=[
        {"canonical_name": "火神", "display_name": "火神", "score": 120.0, "match_reason": "canonical"}
    ])
    facade.build_wiki_link = AsyncMock(return_value="https://wiki.biligame.com/rocokingdomworld/%E7%81%AB%E7%A5%9E")
    return facade


@pytest.fixture
def mock_card_facade() -> MagicMock:
    facade = MagicMock(spec=SpiritCardFacade)
    facade.render_spirit_card = MagicMock(
        return_value=MagicMock(
            html="<div>火神卡片</div>",
            fallback_text="火神 - 火系精灵",
            render_mode="rich_html",
            metadata={"card_version": "v2"},
        )
    )
    return facade


@pytest.fixture
def data_client(mock_data_facade: AsyncMock) -> DataLayerClient:
    return DataLayerClient(mock_data_facade)


@pytest.fixture
def card_client(mock_card_facade: MagicMock) -> SpiritCardClient:
    return SpiritCardClient(mock_card_facade)


@pytest.fixture
def tool_registry(data_client: DataLayerClient, card_client: SpiritCardClient) -> ToolRegistry:
    return ToolRegistry(data_client, card_client)


# ---------------------------------------------------------------------------
# DataLayerClient 集成测试
# ---------------------------------------------------------------------------


class TestDataLayerClient:
    @pytest.mark.asyncio
    async def test_get_spirit_info_success(self, data_client: DataLayerClient):
        """资料查询成功 → 返回结构化资料 + wiki_url。"""
        result = await data_client.get_spirit_info("火神")
        assert result["success"] is True
        assert result["spirit_profile"] is not None
        assert result["wiki_url"] is not None
        assert result["error_message"] is None

    @pytest.mark.asyncio
    async def test_get_spirit_info_not_found_returns_wiki_url(
        self, mock_data_facade: AsyncMock, data_client: DataLayerClient
    ):
        """精灵未找到 → 仍返回 wiki_url 降级信息。"""
        from data_layer.app.errors import SpiritNotFoundError
        mock_data_facade.get_spirit_profile = AsyncMock(
            side_effect=SpiritNotFoundError("not found")
        )
        result = await data_client.get_spirit_info("不存在的精灵")
        assert result["success"] is False
        assert result["spirit_profile"] is None
        assert result["wiki_url"] is not None
        assert "未找到" in result["error_message"]

    @pytest.mark.asyncio
    async def test_get_spirit_info_timeout_returns_wiki_url(
        self, mock_data_facade: AsyncMock, data_client: DataLayerClient
    ):
        """BWIKI 超时 → 仍返回 wiki_url 降级信息。"""
        from data_layer.app.errors import WikiUpstreamTimeoutError
        mock_data_facade.get_spirit_profile = AsyncMock(
            side_effect=WikiUpstreamTimeoutError("timeout", wiki_url="https://test")
        )
        result = await data_client.get_spirit_info("火神")
        assert result["success"] is False
        assert result["wiki_url"] == "https://test"
        assert "超时" in result["error_message"]

    @pytest.mark.asyncio
    async def test_search_wiki_success(self, data_client: DataLayerClient):
        """搜索成功 → 返回候选列表。"""
        result = await data_client.search_wiki("火", limit=5)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["canonical_name"] == "火神"


# ---------------------------------------------------------------------------
# SpiritCardClient 集成测试
# ---------------------------------------------------------------------------


class TestSpiritCardClient:
    @pytest.mark.asyncio
    async def test_render_card_success(self, card_client: SpiritCardClient):
        """卡片渲染成功 → 返回 html/fallback_text/render_mode/metadata。"""
        profile = _make_spirit_profile()
        result = await card_client.render_spirit_card(profile)
        assert result["success"] is True
        assert result["html"] is not None
        assert result["fallback_text"] is not None
        assert result["render_mode"] == "rich_html"
        assert result["metadata"] is not None
        assert result["error_message"] is None

    @pytest.mark.asyncio
    async def test_render_card_failure_returns_fallback(
        self, mock_card_facade: MagicMock, card_client: SpiritCardClient
    ):
        """卡片渲染失败 → 返回 fallback_text 降级信息。"""
        mock_card_facade.render_spirit_card = MagicMock(side_effect=Exception("render error"))
        profile = _make_spirit_profile()
        result = await card_client.render_spirit_card(profile)
        assert result["success"] is False
        assert result["html"] is None
        assert result["fallback_text"] is not None
        assert result["render_mode"] == "text_only"
        assert "渲染失败" in result["error_message"]


# ---------------------------------------------------------------------------
# ToolRegistry 集成测试
# ---------------------------------------------------------------------------


class TestToolRegistry:
    @pytest.mark.asyncio
    async def test_get_spirit_profile_success_full_result(
        self, tool_registry: ToolRegistry
    ):
        """完整成功路径 → 返回资料 + 卡片 + wiki_url。"""
        result = await tool_registry.get_spirit_profile("火神")
        assert result["success"] is True
        assert result["spirit_profile"] is not None
        assert result["card_html"] is not None
        assert result["card_fallback_text"] is not None
        assert result["card_render_mode"] == "rich_html"
        assert result["wiki_url"] is not None
        assert result["error_message"] is None

    @pytest.mark.asyncio
    async def test_get_spirit_profile_data_failure_degrades(
        self, mock_data_facade: AsyncMock, tool_registry: ToolRegistry
    ):
        """资料查询失败 → 返回降级信息，不泄漏内部异常。"""
        from data_layer.app.errors import SpiritNotFoundError
        mock_data_facade.get_spirit_profile = AsyncMock(
            side_effect=SpiritNotFoundError("not found")
        )
        result = await tool_registry.get_spirit_profile("不存在的精灵")
        assert result["success"] is False
        assert result["spirit_profile"] is None
        assert result["card_html"] is None
        assert result["card_fallback_text"] is not None
        assert result["wiki_url"] is not None
        assert result["error_message"] is not None

    @pytest.mark.asyncio
    async def test_get_spirit_profile_card_failure_degrades(
        self, mock_card_facade: MagicMock, tool_registry: ToolRegistry
    ):
        """卡片渲染失败 → 仍返回资料 + fallback 降级。"""
        mock_card_facade.render_spirit_card = MagicMock(side_effect=Exception("render error"))
        result = await tool_registry.get_spirit_profile("火神")
        assert result["success"] is False
        assert result["spirit_profile"] is not None  # 资料成功
        assert result["card_html"] is None
        assert result["card_fallback_text"] is not None
        assert result["card_render_mode"] == "text_only"
        assert result["error_message"] is not None

    @pytest.mark.asyncio
    async def test_search_spirits_success(self, tool_registry: ToolRegistry):
        """搜索成功 → 返回候选列表。"""
        result = await tool_registry.search_spirits("火", limit=5)
        assert result["success"] is True
        assert isinstance(result["candidates"], list)
        assert len(result["candidates"]) >= 1
        assert result["error_message"] is None

    @pytest.mark.asyncio
    async def test_search_spirits_failure_returns_empty(
        self, mock_data_facade: AsyncMock, tool_registry: ToolRegistry
    ):
        """搜索失败 → 返回空列表 + 错误信息。"""
        mock_data_facade.search_spirits = AsyncMock(side_effect=Exception("search error"))
        result = await tool_registry.search_spirits("火", limit=5)
        assert result["success"] is False
        assert result["candidates"] == []
        assert result["error_message"] is not None
