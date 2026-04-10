"""
data-layer-system 核心契约定义

包含所有跨系统共享的领域数据类和 Facade 协议。
agent-backend-system 只依赖此文件中的类型定义，不依赖具体实现。

数据类定义对齐: data-layer-system.md §6.1 Core Entities
协议定义对齐: data-layer-system.md §5.2 Cross-System Interface
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# 6.1 Core Entities
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpiritProfile:
    """精灵结构化资料 — 上游最重要的领域对象。

    字段保持瘦身，只包含 Agent 配队推理真正需要的维度。
    """

    canonical_name: str
    display_name: str
    types: list[str]
    base_stats: dict[str, int]
    skills: list[dict]
    bloodline_type: str | None
    evolution_chain: list[dict]
    wiki_url: str


@dataclass(frozen=True)
class SearchCandidate:
    """名称搜索候选项 — 服务于查无结果与歧义澄清。"""

    canonical_name: str
    display_name: str
    score: float
    match_reason: str


@dataclass(frozen=True)
class TypeMatchupResult:
    """属性克制计算结果 — 来自本地静态知识，不依赖网络。"""

    input_types: list[str]
    attack_advantages: list[dict]
    defense_weaknesses: list[dict]
    defense_resistances: list[dict]


@dataclass(frozen=True)
class StaticKnowledgeEntry:
    """静态机制知识条目 — 本地文件权威源。"""

    topic_key: str
    title: str
    content: str
    source: str


@dataclass
class DataLayerErrorEnvelope:
    """跨系统错误语义载体。

    error_code 前缀对齐 02_ARCHITECTURE_OVERVIEW.md §3.5 错误分类矩阵:
    - SPIRIT_NOT_FOUND_
    - SPIRIT_AMBIGUOUS_
    - WIKI_TIMEOUT_
    - WIKI_PARSE_
    wiki_url 为强制必填，仅当名称完全无法解析时才允许为空字符串。
    """

    error_code: str
    message: str
    retryable: bool
    wiki_url: str
    candidates: list[SearchCandidate] | None = field(default=None)


# ---------------------------------------------------------------------------
# 5.2 Cross-System Interface Protocol
# ---------------------------------------------------------------------------


class IDataLayerFacade(Protocol):
    """数据层对外统一契约 — agent-backend-system 唯一入口。

    所有方法均为 async，返回领域对象或抛出结构化错误。
    """

    async def resolve_spirit_name(self, query: str) -> dict:
        """名称规范化与候选解析。"""
        ...

    async def get_spirit_profile(self, spirit_name: str) -> dict:
        """获取精灵结构化资料。"""
        ...

    async def search_spirits(self, query: str, limit: int = 5) -> list[dict]:
        """搜索精灵候选列表。"""
        ...

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        """属性克制计算。"""
        ...

    async def get_static_knowledge(self, topic_key: str) -> dict:
        """静态机制知识读取。"""
        ...

    async def build_wiki_link(self, spirit_name: str) -> str:
        """构造 BWIKI 页面链接。"""
        ...
