"""
data-layer-system 统一 Facade

agent-backend-system 的唯一数据层入口。
实现 IDataLayerFacade 协议，将名称解析、wiki 查询、静态知识和缓存
组合为一组稳定的领域读取操作。

对齐: data-layer-system.md §4.2 Data Layer Facade、§5.1 操作契约表
"""

from __future__ import annotations

from dataclasses import asdict

from .contracts import IDataLayerFacade, SearchCandidate
from .errors import AmbiguousSpiritNameError, SpiritNotFoundError
from ..cache.key_builder import build_cache_key
from ..cache.registry import CacheRegistry
from ..spirits.alias_index import AliasIndex
from ..spirits.fuzzy_matcher import fuzzy_match
from ..spirits.name_resolver import NameResolver, normalize_text
from ..spirits.repository import SpiritRepository
from ..static.type_chart import TypeMatchupStore
from ..static.mechanism_knowledge import StaticKnowledgeStore
from ..wiki.gateway import WikiGateway
from ..wiki.parser import WikiParser


class DataLayerFacade:
    """数据层 Facade — 统一领域读取入口。

    已接通:
    - get_type_matchup / get_static_knowledge (静态知识)
    - resolve_spirit_name / get_spirit_profile / search_spirits / build_wiki_link
    """

    def __init__(
        self,
        *,
        type_matchup_store: TypeMatchupStore | None = None,
        knowledge_store: StaticKnowledgeStore | None = None,
        name_resolver: NameResolver | None = None,
        spirit_repository: SpiritRepository | None = None,
        cache_registry: CacheRegistry | None = None,
    ) -> None:
        self._type_matchup_store = type_matchup_store or TypeMatchupStore()
        self._knowledge_store = knowledge_store or StaticKnowledgeStore()
        self._cache = cache_registry or CacheRegistry()

        self._resolver = name_resolver or NameResolver(AliasIndex())

        if spirit_repository is not None:
            self._repository = spirit_repository
        else:
            self._repository = SpiritRepository(
                self._resolver,
                WikiGateway(),
                WikiParser(),
                self._cache,
            )

    # ------------------------------------------------------------------
    # 精灵名称与资料
    # ------------------------------------------------------------------

    async def resolve_spirit_name(self, query: str) -> dict:
        """名称规范化与候选解析。

        委托 NameResolver.resolve()，将 SearchCandidate 转为 dict。
        原样透传 SpiritNotFoundError / AmbiguousSpiritNameError。
        """
        result = self._resolver.resolve(query)
        return {
            "status": result["status"],
            "canonical_name": result["canonical_name"],
            "candidates": [asdict(c) for c in result["candidates"]],
        }

    async def get_spirit_profile(self, spirit_name: str) -> dict:
        """获取精灵结构化资料。

        委托 SpiritRepository.get_spirit_profile()，将 SpiritProfile 转为 dict。
        原样透传 SpiritNotFoundError / AmbiguousSpiritNameError /
        WikiUpstreamTimeoutError / WikiParseError。
        """
        profile = await self._repository.get_spirit_profile(spirit_name)
        return asdict(profile)

    async def search_spirits(self, query: str, limit: int = 5) -> list[dict]:
        """搜索精灵候选列表。

        与 resolve_spirit_name 不同：不抛异常，始终返回候选列表（可能为空）。
        优先精确匹配，歧义时返回全部候选，无匹配时模糊搜索。
        结果缓存至 CacheRegistry.search_results。
        """
        cache_key = build_cache_key("search_candidates", f"{query}:{limit}")
        cached = self._cache.search_results.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = self._resolver.resolve(query)
            candidates = result["candidates"]
        except AmbiguousSpiritNameError as exc:
            candidates = exc.candidates
        except SpiritNotFoundError:
            cleaned = normalize_text(query)
            candidates = fuzzy_match(
                cleaned,
                self._resolver.canonical_names,
                limit=limit,
            ) if cleaned else []

        result_list = [asdict(c) for c in candidates]
        self._cache.search_results[cache_key] = result_list
        return result_list

    async def build_wiki_link(self, spirit_name: str) -> str:
        """构造精灵 BWIKI 页面链接。

        委托 SpiritRepository.build_wiki_link()。
        原样透传 SpiritNotFoundError / AmbiguousSpiritNameError。
        """
        return await self._repository.build_wiki_link(spirit_name)

    # ------------------------------------------------------------------
    # 静态知识
    # ------------------------------------------------------------------

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        """属性克制计算 — 纯本地，不依赖网络。"""
        result = self._type_matchup_store.get_type_matchup(type_combo)
        return asdict(result)

    async def get_static_knowledge(self, topic_key: str) -> dict:
        """静态机制知识读取 — 纯本地，不依赖网络。"""
        entry = self._knowledge_store.get_static_knowledge(topic_key)
        return asdict(entry)


# 类型断言: DataLayerFacade 满足 IDataLayerFacade 协议
def _assert_protocol_compliance() -> None:
    facade: IDataLayerFacade = DataLayerFacade()  # noqa: F841
