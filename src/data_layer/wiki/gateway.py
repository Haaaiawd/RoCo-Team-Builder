"""
BWIKI Wiki Gateway — 负责 MediaWiki API 请求、超时与重试边界。

不承载领域逻辑，只负责 HTTP 通信。
对齐: data-layer-system.md §4.2 Wiki Gateway
     data-layer-system.detail.md §1 WIKI_REQUEST_TIMEOUT_SECONDS=5
"""

from __future__ import annotations

import httpx

from ..app.errors import WikiUpstreamTimeoutError
from .endpoint_builder import BWIKI_API_URL, build_parse_api_params, build_wiki_link

WIKI_REQUEST_TIMEOUT_SECONDS: float = 5.0


class WikiGateway:
    """BWIKI MediaWiki API 网关。

    使用 httpx.AsyncClient 发送请求，超时 5s，不做自动重试。
    """

    def __init__(self, *, timeout: float = WIKI_REQUEST_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "User-Agent": "RoCoTeamBuilder/0.1 (wiki data layer; +https://github.com/roco)"
                },
            )
        return self._client

    async def fetch_spirit_page(self, spirit_name: str) -> dict:
        """请求精灵页面的 wikitext。

        Args:
            spirit_name: 规范化后的精灵名称

        Returns:
            MediaWiki API JSON 响应 dict

        Raises:
            WikiUpstreamTimeoutError: 请求超时
        """
        wiki_url = build_wiki_link(spirit_name)
        client = await self._get_client()
        params = build_parse_api_params(spirit_name)

        try:
            response = await client.get(BWIKI_API_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise WikiUpstreamTimeoutError(
                f"BWIKI 请求超时 ({self._timeout}s): {spirit_name}",
                wiki_url=wiki_url,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise WikiUpstreamTimeoutError(
                f"BWIKI 请求失败 (HTTP {exc.response.status_code}): {spirit_name}",
                wiki_url=wiki_url,
            ) from exc

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
