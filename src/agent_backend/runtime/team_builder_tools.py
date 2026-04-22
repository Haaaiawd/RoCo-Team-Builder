"""
配队推理与技能调优工具链 — 为 Agent 提供精灵配队和技能分析能力。

职责：
- 提供精灵资料查询工具（包装 data-layer）
- 提供属性克制查询工具
- 提供静态机制知识查询工具
- 工具返回结构化数据供 Agent 推理使用

对齐: agent-backend-system.md §4.2 Tool Registry、§5.1 工具调用流程
验收标准: T3.2.3 配队推理、追问、技能调优三条路径

设计约束：
本模块只暴露"纯 async 方法"，不直接使用 `@function_tool` 装饰。
`@function_tool` 在 `openai-agents` 安装时会把方法包成 `FunctionTool`
对象（不可直接 `await`），会破坏单元/集成测试对内部协程的直接调用。
因此工具的 `FunctionTool` 包装由 `AgentFactory` 在构造 Agent 时统一完成，
保证 `await tools.method(...)` 在任何环境下都可运行。
"""

from __future__ import annotations

from typing import Annotated, Any

from ..integrations.data_layer_client import IDataLayerClient


class TeamBuilderTools:
    """配队工具集 — 包装 data-layer 能力为 Agent 可调用工具。"""

    def __init__(self, data_client: IDataLayerClient, session_record: Any | None = None) -> None:
        self._data_client = data_client
        self._session_record = session_record
        self._owned_spirits: list[str] = []

    def set_owned_spirits(self, spirit_names: list[str]) -> None:
        """设置用户拥有的精灵列表（从会话读取）。"""
        self._owned_spirits = spirit_names

    def get_owned_spirits(self) -> list[str]:
        """获取用户拥有的精灵列表。"""
        if self._session_record and hasattr(self._session_record, "get_owned_spirits"):
            return self._session_record.get_owned_spirits()
        return self._owned_spirits

    async def get_spirit_info(
        self,
        spirit_name: Annotated[str, "精灵名称（支持别名或模糊匹配）"],
    ) -> dict:
        """获取精灵结构化资料（含 BWIKI 链接）。

        返回资料包括：属性、基础数值、技能列表、血统类型、进化链、BWIKI 链接。
        失败时仍返回带 wiki_url 的降级信息。
        """
        return await self._data_client.get_spirit_info(spirit_name)

    async def search_spirits(
        self,
        query: Annotated[str, "搜索关键词"],
        limit: Annotated[int, "返回候选数量上限"] = 5,
    ) -> dict:
        """搜索精灵候选列表。

        支持精确匹配和模糊匹配，返回候选列表供 Agent 选择。
        如果 owned_spirits 非空，候选池仅从 owned_spirits 内选取。
        """
        owned = self.get_owned_spirits()
        result = await self._data_client.search_wiki(query, limit=limit)

        if owned and result.get("success"):
            candidates = result.get("candidates", [])
            filtered = [c for c in candidates if c.get("canonical_name") in owned]
            result["candidates"] = filtered if filtered else candidates
            if not filtered and candidates:
                result["warning"] = "推荐候选超出用户拥有列表，请确认是否放宽限制"

        return result

    async def get_type_matchup(
        self,
        type_combo: Annotated[list[str], "属性组合列表，如 ['火', '草']"],
    ) -> dict:
        """属性克制计算。

        返回指定属性组合的攻击优势和弱点分析。
        用于配队时的属性互补性分析。
        """
        return await self._data_client.get_type_matchup(type_combo)

    async def get_static_knowledge(
        self,
        topic_key: Annotated[str, "知识主题键，如 'type_chart', 'nature_chart'"],
    ) -> dict:
        """静态机制知识读取。

        返回属性克制表、性格加成表等静态知识。
        用于配队和技能调优时的规则参考。
        """
        return await self._data_client.get_static_knowledge(topic_key)
