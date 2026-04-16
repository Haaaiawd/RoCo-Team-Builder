"""
Agent 工厂 — 创建 RoCo 配队 Agent 实例。

职责：
- 根据 data-layer 客户端创建工具集
- 组装 Agent 实例（instructions + tools）
- 提供 Agent 创建和运行接口

对齐: agent-backend-system.md §4.2 Tool Registry、§4.3 Agent 提示词设计
验收标准: T3.2.3 配队/追问/技能调优三条路径
"""

from __future__ import annotations

from typing import Any, Protocol

try:
    from agents import Agent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    Agent = None  # type: ignore

from ..integrations.data_layer_client import IDataLayerClient
from .prompting import SKILL_TUNING_INSTRUCTIONS, TEAM_BUILDER_INSTRUCTIONS
from .team_builder_tools import TeamBuilderTools


class IAgentFactory(Protocol):
    """Agent 工厂协议。"""

    def create_team_builder_agent(self) -> Agent:
        """创建配队推理 Agent。"""
        ...

    def create_skill_tuning_agent(self) -> Agent:
        """创建技能调优 Agent。"""
        ...


class AgentFactory:
    """RoCo Agent 工厂 — 创建配队和技能调优 Agent。"""

    def __init__(self, data_client: IDataLayerClient, session_record: Any | None = None) -> None:
        self._data_client = data_client
        self._session_record = session_record
        self._tools = TeamBuilderTools(data_client, session_record)

    def set_owned_spirits(self, spirit_names: list[str]) -> None:
        """设置用户拥有的精灵约束（从 session 注入）。"""
        self._tools.set_owned_spirits(spirit_names)

    def create_team_builder_agent(self) -> Agent:
        """创建配队推理 Agent。

        Returns:
            Agent 实例，已注册配队工具（精灵资料查询、搜索、属性克制、静态知识）

        Raises:
            RuntimeError: 如果 openai-agents 包未安装
        """
        if not AGENTS_AVAILABLE:
            raise RuntimeError(
                "openai-agents package not installed. "
                "Install with: pip install openai-agents"
            )
        return Agent(
            name="roco_team_builder",
            instructions=TEAM_BUILDER_INSTRUCTIONS,
            tools=[
                self._tools.get_spirit_info,
                self._tools.search_spirits,
                self._tools.get_type_matchup,
                self._tools.get_static_knowledge,
            ],
        )

    def create_skill_tuning_agent(self) -> Agent:
        """创建技能调优 Agent。

        Returns:
            Agent 实例，已注册技能分析工具

        Raises:
            RuntimeError: 如果 openai-agents 包未安装
        """
        if not AGENTS_AVAILABLE:
            raise RuntimeError(
                "openai-agents package not installed. "
                "Install with: pip install openai-agents"
            )
        return Agent(
            name="roco_skill_tuner",
            instructions=SKILL_TUNING_INSTRUCTIONS,
            tools=[
                self._tools.get_spirit_info,
                self._tools.get_type_matchup,
                self._tools.get_static_knowledge,
            ],
        )
