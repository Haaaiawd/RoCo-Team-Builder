"""
BWIKI Wiki Gateway — 负责 MediaWiki API 请求、超时与重试边界。

不承载领域逻辑，只负责 HTTP 通信。
对齐: data-layer-system.md §4.2 Wiki Gateway
     data-layer-system.detail.md §1 WIKI_REQUEST_TIMEOUT_SECONDS=5

防御措施 (对齐 API:Etiquette + CC BY-NC-SA 4.0 合规):
  - 全局速率限制: asyncio.Semaphore + 请求间隔 ≥ 1s
  - In-flight 去重: 同一精灵名的并发请求复用同一 Future
  - 指数退避: 连续失败时自动延长请求间隔，最大 30s
"""

from __future__ import annotations

import asyncio
import time

import httpx

from ..app.errors import WikiUpstreamTimeoutError
from .endpoint_builder import BWIKI_API_URL, build_parse_api_params, build_wiki_link

WIKI_REQUEST_TIMEOUT_SECONDS: float = 5.0
RATE_LIMIT_MIN_INTERVAL: float = 1.0
BACKOFF_BASE: float = 2.0
BACKOFF_MAX: float = 30.0


class WikiGateway:
    """BWIKI MediaWiki API 网关。

    使用 httpx.AsyncClient 发送请求，超时 5s。
    内置速率限制、in-flight 去重和指数退避，遵守 MediaWiki API 礼仪。
    """

    def __init__(
        self,
        *,
        timeout: float = WIKI_REQUEST_TIMEOUT_SECONDS,
        min_interval: float = RATE_LIMIT_MIN_INTERVAL,
    ) -> None:
        self._timeout = timeout
        self._min_interval = min_interval
        self._client: httpx.AsyncClient | None = None

        self._semaphore = asyncio.Semaphore(1)
        self._last_request_time: float = 0.0
        self._consecutive_failures: int = 0

        self._inflight: dict[str, asyncio.Future[dict]] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "User-Agent": "RoCoTeamBuilder/0.1 (wiki data layer; +https://github.com/roco)"
                },
            )
        return self._client

    async def _wait_rate_limit(self) -> None:
        """等待速率限制间隔 + 退避时间。"""
        backoff = 0.0
        if self._consecutive_failures > 0:
            backoff = min(
                BACKOFF_BASE ** self._consecutive_failures,
                BACKOFF_MAX,
            )

        now = time.monotonic()
        elapsed = now - self._last_request_time
        wait_time = max(self._min_interval + backoff - elapsed, 0)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    async def fetch_spirit_page(self, spirit_name: str) -> dict:
        """请求精灵页面的 wikitext。

        包含 in-flight 去重: 同一 spirit_name 的并发调用共享同一请求。

        Args:
            spirit_name: 规范化后的精灵名称

        Returns:
            MediaWiki API JSON 响应 dict

        Raises:
            WikiUpstreamTimeoutError: 请求超时或 HTTP 错误
        """
        key = spirit_name.strip().lower()

        if key in self._inflight:
            return await self._inflight[key]

        loop = asyncio.get_event_loop()
        future: asyncio.Future[dict] = loop.create_future()
        self._inflight[key] = future

        try:
            result = await self._do_fetch(spirit_name)
            future.set_result(result)
            return result
        except Exception as exc:
            future.set_exception(exc)
            raise
        finally:
            self._inflight.pop(key, None)

    async def _do_fetch(self, spirit_name: str) -> dict:
        """实际执行 HTTP 请求（受速率限制保护）。"""
        wiki_url = build_wiki_link(spirit_name)

        async with self._semaphore:
            await self._wait_rate_limit()
            client = await self._get_client()
            params = build_parse_api_params(spirit_name)

            try:
                self._last_request_time = time.monotonic()
                response = await client.get(BWIKI_API_URL, params=params)
                response.raise_for_status()
                self._consecutive_failures = 0
                return response.json()
            except httpx.TimeoutException as exc:
                self._consecutive_failures += 1
                raise WikiUpstreamTimeoutError(
                    f"BWIKI 请求超时 ({self._timeout}s): {spirit_name}",
                    wiki_url=wiki_url,
                ) from exc
            except httpx.HTTPStatusError as exc:
                self._consecutive_failures += 1
                raise WikiUpstreamTimeoutError(
                    f"BWIKI 请求失败 (HTTP {exc.response.status_code}): {spirit_name}",
                    wiki_url=wiki_url,
                ) from exc

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
