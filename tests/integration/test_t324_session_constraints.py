"""
T3.2.4 集成测试 — 截图识别确认流与 owned_spirits 会话约束。

验收标准:
  - Given 用户上传精灵列表截图 → When Agent 调用 recognize_spirit_list 工具 → Then 返回结构化 RecognitionResult
  - Given 用户确认精灵列表 → When 确认信号被接收 → Then owned_spirits 写入当前会话上下文
  - Given owned_spirits 非空时 Agent 执行配队推理 → When recommend_team 调用候选池 → Then 候选只从 owned_spirits 内选取
  - Given 截图中存在模糊或遮挡的精灵名称 → When 识别置信度低于阈值 → Then RecognitionResult.uncertain_items 非空
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agent_backend.app.session_extensions import SessionRecordExtended
from agent_backend.runtime.recognition_tool import RecognitionResult, recognize_spirit_list
from agent_backend.runtime.team_builder_tools import TeamBuilderTools


class TestRecognitionTool:
    def test_recognize_spirit_list_basic(self):
        """基础识别测试 — 返回结构化 RecognitionResult。"""
        result = recognize_spirit_list("火神 冰龙王", confidence_threshold=0.8)
        assert isinstance(result, dict)
        assert "spirit_names" in result
        assert "uncertain_items" in result
        assert "confidence_threshold" in result
        assert result["confidence_threshold"] == 0.8

    def test_recognize_spirit_list_with_uncertainty(self):
        """不确定项测试 — 模糊或遮挡的精灵归入 uncertain_items。"""
        result = recognize_spirit_list("火神 水灵", confidence_threshold=0.8)
        assert "水灵" in result.get("uncertain_items", [])


class TestSessionExtensions:
    def test_session_record_extended_initialization(self):
        """SessionRecordExtended 初始化应包含 owned_spirits 字段。"""
        record = SessionRecordExtended(session_key="user:chat")
        assert hasattr(record, "owned_spirits")
        assert record.owned_spirits == []
        assert not record.has_owned_spirits()

    def test_set_and_get_owned_spirits(self):
        """设置和获取 owned_spirits。"""
        record = SessionRecordExtended(session_key="user:chat")
        record.set_owned_spirits(["火神", "冰龙王", "水灵"])
        assert record.get_owned_spirits() == ["火神", "冰龙王", "水灵"]
        assert record.has_owned_spirits()


class TestTeamBuilderToolsConstraints:
    @pytest.fixture
    def mock_data_client(self) -> AsyncMock:
        client = AsyncMock()
        client.search_wiki = AsyncMock(return_value={
            "success": True,
            "candidates": [
                {"canonical_name": "火神", "display_name": "火神", "score": 100.0},
                {"canonical_name": "冰龙王", "display_name": "冰龙王", "score": 95.0},
                {"canonical_name": "水灵", "display_name": "水灵", "score": 90.0},
            ]
        })
        return client

    @pytest.fixture
    def session_record(self) -> SessionRecordExtended:
        record = SessionRecordExtended(session_key="user:chat")
        record.set_owned_spirits(["火神", "冰龙王"])
        return record

    @pytest.fixture
    def tools(self, mock_data_client: AsyncMock, session_record: SessionRecordExtended) -> TeamBuilderTools:
        return TeamBuilderTools(mock_data_client, session_record)

    @pytest.mark.asyncio
    async def test_search_spirits_filters_by_owned(self, tools: TeamBuilderTools):
        """owned_spirits 非空时，候选池仅从 owned_spirits 内选取。"""
        result = await tools.search_spirits("火", limit=5)
        candidates = result.get("candidates", [])
        canonical_names = [c.get("canonical_name") for c in candidates]
        # 应该只包含 owned_spirits 中的精灵
        assert all(name in ["火神", "冰龙王"] for name in canonical_names)

    @pytest.mark.asyncio
    async def test_search_spirits_warning_when_filtered_empty(self, mock_data_client: AsyncMock):
        """过滤后候选为空时，应添加警告提示。"""
        mock_data_client.search_wiki = AsyncMock(return_value={
            "success": True,
            "candidates": [
                {"canonical_name": "冰龙王", "display_name": "冰龙王", "score": 95.0},
            ]
        })
        record = SessionRecordExtended(session_key="user:chat")
        record.set_owned_spirits(["火神"])  # 只有火神，但搜索结果只有冰龙王
        tools = TeamBuilderTools(mock_data_client, record)

        result = await tools.search_spirits("冰", limit=5)
        # 过滤后为空，应返回原候选 + 警告
        assert result.get("warning") is not None
        assert "超出用户拥有列表" in result["warning"]

    @pytest.mark.asyncio
    async def test_search_spirits_no_constraint_when_owned_empty(self, mock_data_client: AsyncMock):
        """owned_spirits 为空时，不过滤候选池。"""
        record = SessionRecordExtended(session_key="user:chat")
        tools = TeamBuilderTools(mock_data_client, record)

        result = await tools.search_spirits("火", limit=5)
        candidates = result.get("candidates", [])
        # 应该返回所有候选，不过滤
        assert len(candidates) == 3

    def test_set_owned_spirits_from_session(self, session_record: SessionRecordExtended, mock_data_client: AsyncMock):
        """从会话设置 owned_spirits。"""
        tools = TeamBuilderTools(mock_data_client, session_record)
        owned = tools.get_owned_spirits()
        assert owned == ["火神", "冰龙王"]

    def test_set_owned_spirits_directly(self, mock_data_client: AsyncMock):
        """直接设置 owned_spirits。"""
        tools = TeamBuilderTools(mock_data_client, session_record=None)
        tools.set_owned_spirits(["火神", "冰龙王"])
        owned = tools.get_owned_spirits()
        assert owned == ["火神", "冰龙王"]
