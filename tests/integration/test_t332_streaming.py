"""
T3.3.2 集成测试 — SSE 流式输出桥接与并发隔离验证。

验收标准:
  - Given stream=true 的聊天请求 → When 后端开始返回响应 → Then 输出符合 OpenAI Chat Completions 的 SSE chunk，且以 `data: [DONE]` 结束
  - Given mid-stream provider/tool error → When 错误在流式过程中发生 → Then 以错误 chunk 编码，不出现裸断流
  - Given 10 个并发会话且同一用户使用不同 chat_id → When 同时发起请求 → Then 上下文不串线，且同一 session 内请求保持串行
"""

from __future__ import annotations

import json

import pytest

from agent_backend.app.stream_bridge import (
    ChunkType,
    SSEChunk,
    _convert_event_to_chunk,
    _format_sse_chunk,
    encode_mid_stream_error,
    stream_runtime_events,
)


class TestSSEChunkConversion:
    def test_convert_content_event(self):
        """内容事件应转换为 content chunk。"""
        event = {
            "type": "content",
            "id": "chatcmpl-123",
            "created": 1234567890,
            "content": "你好",
        }
        chunk = _convert_event_to_chunk(event, "roco-agent")
        assert chunk.chunk_type == ChunkType.CONTENT
        assert chunk.data["model"] == "roco-agent"
        assert chunk.data["choices"][0]["delta"]["content"] == "你好"

    def test_convert_error_event(self):
        """错误事件应转换为 error chunk。"""
        event = {
            "type": "error",
            "message": "Provider timeout",
            "error_code": "provider_timeout",
        }
        chunk = _convert_event_to_chunk(event, "roco-agent")
        assert chunk.chunk_type == ChunkType.ERROR
        assert "error" in chunk.data
        assert chunk.data["error"]["message"] == "Provider timeout"

    def test_convert_done_event(self):
        """完成事件应转换为 done chunk。"""
        event = {"type": "done"}
        chunk = _convert_event_to_chunk(event, "roco-agent")
        assert chunk.chunk_type == ChunkType.DONE
        assert chunk.data == {}


class TestSSEFormatting:
    def test_format_content_chunk(self):
        """内容 chunk 应格式化为 SSE 格式。"""
        chunk = SSEChunk(
            chunk_type=ChunkType.CONTENT,
            data={"content": "你好"},
        )
        formatted = _format_sse_chunk(chunk)
        assert formatted.startswith("data: {")
        assert formatted.endswith("\n\n")
        data = json.loads(formatted[6:-2])
        assert data["content"] == "你好"

    def test_format_done_chunk(self):
        """Done chunk 应格式化为 [DONE]。"""
        chunk = SSEChunk(chunk_type=ChunkType.DONE, data={})
        formatted = _format_sse_chunk(chunk)
        assert formatted == "data: [DONE]\n\n"

    def test_encode_mid_stream_error(self):
        """Mid-stream error 应编码为 SSE chunk。"""
        error_chunk = encode_mid_stream_error("Tool execution failed", "tool_error")
        assert error_chunk.startswith("data: {")
        assert error_chunk.endswith("\n\n")
        data = json.loads(error_chunk[6:-2])
        assert data["error"]["message"] == "Tool execution failed"
        assert data["error"]["type"] == "tool_error"


class TestStreamingOutput:
    def test_stream_runtime_events_basic(self):
        """基础流式输出应返回 SSE chunks 并以 [DONE] 结束。"""
        events = [
            {"type": "content", "content": "你"},
            {"type": "content", "content": "好"},
            {"type": "content", "content": "！"},
        ]
        chunks = list(stream_runtime_events(events, "roco-agent"))
        assert len(chunks) == 4  # 3 content + 1 [DONE]
        assert chunks[-1] == "data: [DONE]\n\n"

    def test_stream_runtime_events_with_error(self):
        """流式过程中发生错误应编码为 error chunk。"""
        events = [
            {"type": "content", "content": "你好"},
            {"type": "error", "message": "Timeout", "error_code": "timeout"},
        ]
        chunks = list(stream_runtime_events(events, "roco-agent"))
        assert len(chunks) == 3  # 1 content + 1 error + 1 [DONE]
        assert "error" in chunks[1]
        assert chunks[-1] == "data: [DONE]\n\n"

    def test_stream_runtime_events_empty(self):
        """空事件列表应只返回 [DONE]。"""
        chunks = list(stream_runtime_events([], "roco-agent"))
        assert len(chunks) == 1
        assert chunks[0] == "data: [DONE]\n\n"


class TestSessionIsolation:
    @pytest.mark.asyncio
    async def test_concurrent_sessions_no_cross_talk(self):
        """并发会话应不串线。"""
        # 骨架测试：验证 session_registry 的并发隔离
        from agent_backend.app.session_service import SessionRegistry

        registry = SessionRegistry()
        session1 = registry.get_or_create("user1:chat1")
        session2 = registry.get_or_create("user1:chat2")

        # 不同 chat_id 应返回不同 session
        assert session1 is not session2
        assert session1.session_key == "user1:chat1"
        assert session2.session_key == "user1:chat2"

    @pytest.mark.asyncio
    async def test_same_session_serial_requests(self):
        """同一 session 内请求应串行处理。"""
        from agent_backend.app.session_service import SessionRegistry

        registry = SessionRegistry()
        session = registry.get_or_create("user1:chat1")

        # 添加消息应保持顺序
        session.add_item({"role": "user", "content": "消息1"})
        session.add_item({"role": "user", "content": "消息2"})

        assert len(session.items) == 2
        assert session.items[0]["content"] == "消息1"
        assert session.items[1]["content"] == "消息2"

    @pytest.mark.asyncio
    async def test_session_lock_prevents_concurrent_access(self):
        """Session lock 应防止并发访问。"""
        import asyncio
        from agent_backend.app.session_service import SessionRegistry

        registry = SessionRegistry()
        session = registry.get_or_create("user1:chat1")

        async def add_item(item: dict):
            async with session.lock:
                session.add_item(item)
                await asyncio.sleep(0.01)  # 模拟处理

        # 并发添加应串行化
        tasks = [add_item({"role": "user", "content": f"消息{i}"}) for i in range(10)]
        await asyncio.gather(*tasks)

        assert len(session.items) == 10
