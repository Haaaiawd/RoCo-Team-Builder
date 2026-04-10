"""
data-layer-system 统一 Facade

agent-backend-system 的唯一数据层入口。
实现 IDataLayerFacade 协议，将名称解析、wiki 查询、静态知识和缓存
组合为一组稳定的领域读取操作。

对齐: data-layer-system.md §4.2 Data Layer Facade、§5.1 操作契约表
"""

from __future__ import annotations

from .contracts import (
    IDataLayerFacade,
)


class DataLayerFacade:
    """数据层 Facade — 骨架实现，待后续任务逐步填充。

    当前仅建立模块结构与导入路径，确保 agent-backend-system
    可以按协议导入 IDataLayerFacade 并获取该实现类。
    """

    async def resolve_spirit_name(self, query: str) -> dict:
        raise NotImplementedError("T1.1.2 will implement")

    async def get_spirit_profile(self, spirit_name: str) -> dict:
        raise NotImplementedError("T1.2.1 will implement")

    async def search_spirits(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError("T1.1.2 will implement")

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        raise NotImplementedError("T1.2.2 will implement")

    async def get_static_knowledge(self, topic_key: str) -> dict:
        raise NotImplementedError("T1.2.2 will implement")

    async def build_wiki_link(self, spirit_name: str) -> str:
        raise NotImplementedError("T1.2.1 will implement")


# 类型断言: DataLayerFacade 满足 IDataLayerFacade 协议
def _assert_protocol_compliance() -> None:
    facade: IDataLayerFacade = DataLayerFacade()  # noqa: F841
