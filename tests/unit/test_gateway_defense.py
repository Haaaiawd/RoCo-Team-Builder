"""
WikiGateway 防御机制测试 — 速率限制、in-flight 去重、指数退避。
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from data_layer.wiki.gateway import WikiGateway, RATE_LIMIT_MIN_INTERVAL
from data_layer.app.errors import WikiUpstreamTimeoutError


MOCK_RESPONSE = {
    "parse": {"title": "测试", "wikitext": {"*": "|系别=火\n|精力=80"}}
}


class TestInFlightDedup:
    @pytest.mark.asyncio
    async def test_concurrent_same_spirit_shares_request(self):
        """同一精灵的并发请求应只发出一次 HTTP 调用。"""
        gw = WikiGateway(min_interval=0)

        call_count = 0

        async def mock_do_fetch(spirit_name: str) -> dict:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return MOCK_RESPONSE

        gw._do_fetch = mock_do_fetch  # type: ignore

        results = await asyncio.gather(
            gw.fetch_spirit_page("火神"),
            gw.fetch_spirit_page("火神"),
            gw.fetch_spirit_page("火神"),
        )

        assert call_count == 1
        assert all(r == MOCK_RESPONSE for r in results)

    @pytest.mark.asyncio
    async def test_different_spirits_are_separate_requests(self):
        """不同精灵名的请求应独立发出。"""
        gw = WikiGateway(min_interval=0)

        call_names: list[str] = []

        async def mock_do_fetch(spirit_name: str) -> dict:
            call_names.append(spirit_name)
            await asyncio.sleep(0.01)
            return MOCK_RESPONSE

        gw._do_fetch = mock_do_fetch  # type: ignore

        await asyncio.gather(
            gw.fetch_spirit_page("火神"),
            gw.fetch_spirit_page("冰龙王"),
        )

        assert len(call_names) == 2
        assert "火神" in call_names
        assert "冰龙王" in call_names


class TestExponentialBackoff:
    @pytest.mark.asyncio
    async def test_consecutive_failures_increase_wait(self):
        """连续失败时退避时间应递增。"""
        gw = WikiGateway(min_interval=0)
        gw._consecutive_failures = 0

        gw._consecutive_failures = 3
        gw._last_request_time = 0.0

        import time
        with patch("data_layer.wiki.gateway.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with patch("data_layer.wiki.gateway.time.monotonic", return_value=100.0):
                await gw._wait_rate_limit()

            if mock_sleep.called:
                wait_arg = mock_sleep.call_args[0][0]
                assert wait_arg >= 0

    @pytest.mark.asyncio
    async def test_success_resets_failure_counter(self):
        """成功请求后连续失败计数器应归零。"""
        gw = WikiGateway(min_interval=0)
        gw._consecutive_failures = 5

        async def mock_do_fetch(spirit_name: str) -> dict:
            gw._consecutive_failures = 0
            return MOCK_RESPONSE

        gw._do_fetch = mock_do_fetch  # type: ignore
        await gw.fetch_spirit_page("火神")
        assert gw._consecutive_failures == 0


class TestInFlightErrorPropagation:
    @pytest.mark.asyncio
    async def test_inflight_error_propagates_to_all_waiters(self):
        """in-flight 请求失败时，所有等待者都应收到异常。"""
        gw = WikiGateway(min_interval=0)

        async def mock_do_fetch(spirit_name: str) -> dict:
            await asyncio.sleep(0.05)
            raise WikiUpstreamTimeoutError("timeout", wiki_url="https://test")

        gw._do_fetch = mock_do_fetch  # type: ignore

        results = await asyncio.gather(
            gw.fetch_spirit_page("火神"),
            gw.fetch_spirit_page("火神"),
            return_exceptions=True,
        )

        assert all(isinstance(r, WikiUpstreamTimeoutError) for r in results)
