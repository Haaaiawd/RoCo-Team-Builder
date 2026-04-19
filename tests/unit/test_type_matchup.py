"""
T1.2.2 单元测试 — 属性克制矩阵与静态知识 facade。

验收标准:
  - Given 1-2 个合法属性 → 返回克制/被克制/抗性结果，不依赖网络
  - Given 受支持的 topic_key → 返回结构化静态知识条目与来源字段
  - Given 非法属性组合或未知 topic_key → 返回结构化领域错误
"""

from __future__ import annotations

import pytest

from data_layer.app.contracts import TypeMatchupResult, StaticKnowledgeEntry
from data_layer.app.errors import InvalidTypeComboError, KnowledgeTopicNotFoundError
from data_layer.app.facade import DataLayerFacade
from data_layer.static.type_chart import TypeMatchupStore
from data_layer.static.mechanism_knowledge import StaticKnowledgeStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def store() -> TypeMatchupStore:
    return TypeMatchupStore()


@pytest.fixture
def knowledge() -> StaticKnowledgeStore:
    return StaticKnowledgeStore()


@pytest.fixture
def facade() -> DataLayerFacade:
    return DataLayerFacade()


# ---------------------------------------------------------------------------
# TypeMatchupStore 单元测试
# ---------------------------------------------------------------------------


class TestTypeMatchupStore:
    def test_single_type_attack_advantages(self, store: TypeMatchupStore):
        """火克制草/冰/虫/机械。"""
        result = store.get_type_matchup(["火"])
        assert isinstance(result, TypeMatchupResult)
        assert result.input_types == ["火"]
        targets = {a["target_type"] for a in result.attack_advantages}
        assert "草" in targets
        assert "冰" in targets
        assert "虫" in targets
        assert "机械" in targets

    def test_single_type_defense_weaknesses(self, store: TypeMatchupStore):
        """火弱于水/岩石。"""
        result = store.get_type_matchup(["火"])
        sources = {w["source_type"] for w in result.defense_weaknesses}
        assert "水" in sources
        assert "岩石" in sources

    def test_dual_type_combo(self, store: TypeMatchupStore):
        """双属性组合应合并克制关系。"""
        result = store.get_type_matchup(["火", "龙"])
        assert len(result.input_types) == 2
        attack_targets = {a["target_type"] for a in result.attack_advantages}
        assert "草" in attack_targets
        assert "龙" in attack_targets

    def test_dual_type_weakness_stacking(self, store: TypeMatchupStore):
        """草+冰: 都弱于火, 火应有 4x 弱点。"""
        result = store.get_type_matchup(["草", "冰"])
        fire_weakness = [w for w in result.defense_weaknesses if w["source_type"] == "火"]
        assert len(fire_weakness) == 1
        assert fire_weakness[0]["multiplier"] == 4.0

    def test_empty_combo_raises_error(self, store: TypeMatchupStore):
        with pytest.raises(InvalidTypeComboError):
            store.get_type_matchup([])

    def test_too_many_types_raises_error(self, store: TypeMatchupStore):
        with pytest.raises(InvalidTypeComboError):
            store.get_type_matchup(["火", "水", "草"])

    def test_unknown_type_raises_error(self, store: TypeMatchupStore):
        with pytest.raises(InvalidTypeComboError) as exc_info:
            store.get_type_matchup(["超能力"])
        assert "超能力" in str(exc_info.value)

    def test_valid_types_property(self, store: TypeMatchupStore):
        types = store.valid_types
        assert "火" in types
        assert "水" in types
        assert len(types) >= 16


# ---------------------------------------------------------------------------
# StaticKnowledgeStore 单元测试
# ---------------------------------------------------------------------------


class TestStaticKnowledgeStore:
    def test_type_chart_knowledge(self, knowledge: StaticKnowledgeStore):
        """type_chart 应返回包含属性信息的知识条目。"""
        entry = knowledge.get_static_knowledge("type_chart")
        assert isinstance(entry, StaticKnowledgeEntry)
        assert entry.topic_key == "type_chart"
        assert entry.title == "属性克制表"
        assert "属性" in entry.content
        assert entry.source

    def test_nature_chart_knowledge(self, knowledge: StaticKnowledgeStore):
        """nature_chart 应返回包含性格信息的知识条目。"""
        entry = knowledge.get_static_knowledge("nature_chart")
        assert isinstance(entry, StaticKnowledgeEntry)
        assert entry.topic_key == "nature_chart"
        assert "性格" in entry.content

    def test_placeholder_topics(self, knowledge: StaticKnowledgeStore):
        """预留 topic 应返回占位内容而非报错。"""
        entry = knowledge.get_static_knowledge("bloodline_rules")
        assert isinstance(entry, StaticKnowledgeEntry)
        assert entry.source == "placeholder"

    def test_unknown_topic_raises_error(self, knowledge: StaticKnowledgeStore):
        with pytest.raises(KnowledgeTopicNotFoundError) as exc_info:
            knowledge.get_static_knowledge("不存在的主题")
        assert "不存在的主题" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Facade 集成（T1.2.2 验收标准）
# ---------------------------------------------------------------------------


class TestFacadeStaticKnowledge:
    @pytest.mark.asyncio
    async def test_get_type_matchup_via_facade(self, facade: DataLayerFacade):
        """Facade.get_type_matchup 返回 dict 且不依赖网络。"""
        result = await facade.get_type_matchup(["水"])
        assert isinstance(result, dict)
        assert result["input_types"] == ["水"]
        assert len(result["attack_advantages"]) > 0

    @pytest.mark.asyncio
    async def test_get_static_knowledge_via_facade(self, facade: DataLayerFacade):
        """Facade.get_static_knowledge 返回 dict 且包含 source 字段。"""
        result = await facade.get_static_knowledge("type_chart")
        assert isinstance(result, dict)
        assert "source" in result
        assert "topic_key" in result

    @pytest.mark.asyncio
    async def test_facade_invalid_type_raises_error(self, facade: DataLayerFacade):
        with pytest.raises(InvalidTypeComboError):
            await facade.get_type_matchup(["假属性"])

    @pytest.mark.asyncio
    async def test_facade_unknown_topic_raises_error(self, facade: DataLayerFacade):
        with pytest.raises(KnowledgeTopicNotFoundError):
            await facade.get_static_knowledge("fake_topic")
