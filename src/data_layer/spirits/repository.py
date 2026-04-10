"""
精灵仓储 — 组合名称解析、wiki 网关、解析器与缓存，输出稳定 SpiritProfile。

对齐: data-layer-system.md §4.2 Spirit Repository
     data-layer-system.detail.md §3.2 get_spirit_profile 伪代码
"""

from __future__ import annotations

from ..app.contracts import SpiritProfile
from ..app.errors import WikiParseError, WikiUpstreamTimeoutError
from ..cache.key_builder import build_cache_key
from ..cache.registry import CacheRegistry
from ..wiki.endpoint_builder import build_wiki_link
from ..wiki.gateway import WikiGateway
from ..wiki.parser import WikiParser
from .name_resolver import NameResolver


class SpiritRepository:
    """精灵数据仓储 — 对外提供 get_spirit_profile 与 build_wiki_link。"""

    def __init__(
        self,
        name_resolver: NameResolver,
        wiki_gateway: WikiGateway,
        wiki_parser: WikiParser,
        cache_registry: CacheRegistry,
    ) -> None:
        self._resolver = name_resolver
        self._gateway = wiki_gateway
        self._parser = wiki_parser
        self._cache = cache_registry

    async def get_spirit_profile(self, spirit_name: str) -> SpiritProfile:
        """获取精灵结构化资料。

        流程: 名称解析 → 缓存查找 → wiki 请求 → 解析 → 缓存写入
        失败时必须携带 wiki_url 回退链接。

        Raises:
            SpiritNotFoundError: 名称无法解析
            AmbiguousSpiritNameError: 名称存在歧义
            WikiUpstreamTimeoutError: BWIKI 超时
            WikiParseError: 页面解析失败
        """
        resolved = self._resolver.resolve(spirit_name)
        canonical_name = resolved["canonical_name"]

        cache_key = build_cache_key("spirit_profile", canonical_name)
        cached = self._cache.spirit_profiles.get(cache_key)
        if cached is not None:
            return cached

        wiki_url = build_wiki_link(canonical_name)

        try:
            raw_payload = await self._gateway.fetch_spirit_page(canonical_name)
        except WikiUpstreamTimeoutError:
            raise
        except Exception as exc:
            raise WikiUpstreamTimeoutError(
                f"BWIKI 请求异常: {canonical_name}",
                wiki_url=wiki_url,
            ) from exc

        try:
            profile = self._parser.parse_spirit_profile(raw_payload, wiki_url)
        except WikiParseError:
            raise
        except Exception as exc:
            raise WikiParseError(
                f"解析精灵页面失败: {canonical_name}",
                wiki_url=wiki_url,
            ) from exc

        self._cache.spirit_profiles[cache_key] = profile
        return profile

    async def build_wiki_link(self, spirit_name: str) -> str:
        """构造精灵 BWIKI 页面链接。"""
        resolved = self._resolver.resolve(spirit_name)
        return build_wiki_link(resolved["canonical_name"])
