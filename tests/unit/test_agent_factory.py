"""
T3.2.3 单元测试 — Agent 工厂与工具注册验证。

验收标准:
  - Agent 工厂创建配队 Agent 并注册正确工具
  - Agent 工厂创建技能调优 Agent 并注册正确工具
  - 工具函数具有正确的签名和描述
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agent_backend.runtime.agent_factory import AgentFactory, AGENTS_AVAILABLE
from agent_backend.runtime.team_builder_tools import TeamBuilderTools


@pytest.fixture
def mock_data_client() -> AsyncMock:
    client = AsyncMock()
    client.get_spirit_info = AsyncMock(return_value={"success": True, "spirit_profile": {}, "wiki_url": "https://test"})
    client.search_wiki = AsyncMock(return_value=[])
    client.get_type_matchup = AsyncMock(return_value={})
    client.get_static_knowledge = AsyncMock(return_value={})
    return client


@pytest.fixture
def agent_factory(mock_data_client: AsyncMock) -> AgentFactory:
    return AgentFactory(mock_data_client)


class TestTeamBuilderTools:
    def test_tools_initialization(self, mock_data_client: AsyncMock):
        """工具集初始化应接收 data_client。"""
        tools = TeamBuilderTools(mock_data_client)
        assert tools._data_client is mock_data_client

    def test_get_spirit_info_is_function_tool(self, mock_data_client: AsyncMock):
        """get_spirit_info 应是可调用的 function_tool。"""
        tools = TeamBuilderTools(mock_data_client)
        assert callable(tools.get_spirit_info)
        assert hasattr(tools.get_spirit_info, "__name__")

    def test_search_spirits_is_function_tool(self, mock_data_client: AsyncMock):
        """search_spirits 应是可调用的 function_tool。"""
        tools = TeamBuilderTools(mock_data_client)
        assert callable(tools.search_spirits)
        assert hasattr(tools.search_spirits, "__name__")

    def test_get_type_matchup_is_function_tool(self, mock_data_client: AsyncMock):
        """get_type_matchup 应是可调用的 function_tool。"""
        tools = TeamBuilderTools(mock_data_client)
        assert callable(tools.get_type_matchup)
        assert hasattr(tools.get_type_matchup, "__name__")

    def test_get_static_knowledge_is_function_tool(self, mock_data_client: AsyncMock):
        """get_static_knowledge 应是可调用的 function_tool。"""
        tools = TeamBuilderTools(mock_data_client)
        assert callable(tools.get_static_knowledge)
        assert hasattr(tools.get_static_knowledge, "__name__")


class TestAgentFactory:
    def test_factory_initialization(self, mock_data_client: AsyncMock):
        """工厂初始化应接收 data_client 并创建工具集。"""
        factory = AgentFactory(mock_data_client, session_record=None)
        assert factory._data_client is mock_data_client
        assert isinstance(factory._tools, TeamBuilderTools)

    @pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents not installed")
    def test_create_team_builder_agent(self, agent_factory: AgentFactory):
        """创建配队 Agent 应返回 Agent 实例。"""
        agent = agent_factory.create_team_builder_agent()
        assert agent is not None
        assert agent.name == "roco_team_builder"
        assert "配队专家" in agent.instructions
        assert len(agent.tools) == 4  # 4 个工具

    @pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents not installed")
    def test_team_builder_agent_tools_registered(self, agent_factory: AgentFactory):
        """配队 Agent 应注册 4 个工具。"""
        agent = agent_factory.create_team_builder_agent()
        tool_names = [tool.name for tool in agent.tools]
        assert "get_spirit_info" in tool_names
        assert "search_spirits" in tool_names
        assert "get_type_matchup" in tool_names
        assert "get_static_knowledge" in tool_names

    @pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents not installed")
    def test_create_skill_tuning_agent(self, agent_factory: AgentFactory):
        """创建技能调优 Agent 应返回 Agent 实例。"""
        agent = agent_factory.create_skill_tuning_agent()
        assert agent is not None
        assert agent.name == "roco_skill_tuner"
        assert "技能调优" in agent.instructions
        assert len(agent.tools) == 3  # 3 个工具（不需要 search_spirits）

    @pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents not installed")
    def test_skill_tuning_agent_tools_registered(self, agent_factory: AgentFactory):
        """技能调优 Agent 应注册 3 个工具。"""
        agent = agent_factory.create_skill_tuning_agent()
        tool_names = [tool.name for tool in agent.tools]
        assert "get_spirit_info" in tool_names
        assert "get_type_matchup" in tool_names
        assert "get_static_knowledge" in tool_names
        assert "search_spirits" not in tool_names  # 技能调优不需要搜索

    @pytest.mark.skipif(AGENTS_AVAILABLE, reason="openai-agents is installed")
    def test_create_agent_raises_without_package(self, agent_factory: AgentFactory):
        """openai-agents 未安装时，创建 Agent 应抛 RuntimeError。"""
        with pytest.raises(RuntimeError, match="openai-agents package not installed"):
            agent_factory.create_team_builder_agent()
        with pytest.raises(RuntimeError, match="openai-agents package not installed"):
            agent_factory.create_skill_tuning_agent()
