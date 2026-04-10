"""
data-layer-system 统一 Facade

agent-backend-system 的唯一数据层入口。
实现 IDataLayerFacade 协议，将名称解析、wiki 查询、静态知识和缓存
组合为一组稳定的领域读取操作。

对齐: data-layer-system.md §4.2 Data Layer Facade、§5.1 操作契约表
"""

from __future__ import annotations

from dataclasses import asdict

from .contracts import IDataLayerFacade
from ..static.type_chart import TypeMatchupStore
from ..static.mechanism_knowledge import StaticKnowledgeStore


class DataLayerFacade:
    """数据层 Facade — 逐步填充实现。

    当前已接通:
    - T1.2.2: get_type_matchup / get_static_knowledge (静态知识)
    """

    def __init__(
        self,
        *,
        type_matchup_store: TypeMatchupStore | None = None,
        knowledge_store: StaticKnowledgeStore | None = None,
    ) -> None:
        self._type_matchup_store = type_matchup_store or TypeMatchupStore()
        self._knowledge_store = knowledge_store or StaticKnowledgeStore()

    async def resolve_spirit_name(self, query: str) -> dict:
        raise NotImplementedError("T1.1.2 will implement")

    async def get_spirit_profile(self, spirit_name: str) -> dict:
        raise NotImplementedError("T1.2.1 will implement")

    async def search_spirits(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError("T1.1.2 will implement")

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        """属性克制计算 — 纯本地，不依赖网络。"""
        result = self._type_matchup_store.get_type_matchup(type_combo)
        return asdict(result)

    async def get_static_knowledge(self, topic_key: str) -> dict:
        """静态机制知识读取 — 纯本地，不依赖网络。"""
        entry = self._knowledge_store.get_static_knowledge(topic_key)
        return asdict(entry)

    async def build_wiki_link(self, spirit_name: str) -> str:
        raise NotImplementedError("T1.2.1 will implement")


# 类型断言: DataLayerFacade 满足 IDataLayerFacade 协议
def _assert_protocol_compliance() -> None:
    facade: IDataLayerFacade = DataLayerFacade()  # noqa: F841
