"""
SSE 流式输出桥接 — 将 runtime events 转换为 OpenAI 兼容的 SSE chunk。

职责：
- 将 runtime events 转换为 OpenAI Chat Completions SSE 格式
- 处理 mid-stream error 编码
- 确保以 `data: [DONE]` 结束

对齐: agent-backend-system.md §5.1 stream_runtime_events、§8.2 SSE 格式
验收标准: T3.3.2 流式输出符合 OpenAI 规范，mid-stream error 编码正确
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator


class ChunkType(Enum):
    """SSE chunk 类型。"""

    CONTENT = "content"
    ERROR = "error"
    DONE = "done"


@dataclass
class SSEChunk:
    """SSE chunk 数据结构。"""

    chunk_type: ChunkType
    data: dict[str, Any]


def stream_runtime_events(
    events: list[dict[str, Any]],
    model_id: str,
) -> Generator[str, None, None]:
    """将 runtime events 转换为 SSE chunk 流。

    对齐: agent-backend-system.md §5.1 stream_runtime_events

    Args:
        events: runtime events 列表
        model_id: 模型 ID

    Yields:
        SSE 格式的字符串 chunk
    """
    for event in events:
        chunk = _convert_event_to_chunk(event, model_id)
        yield _format_sse_chunk(chunk)

    # 发送 [DONE] 标记
    yield "data: [DONE]\n\n"


def _convert_event_to_chunk(event: dict[str, Any], model_id: str) -> SSEChunk:
    """将单个 event 转换为 SSEChunk。"""
    event_type = event.get("type", "content")

    if event_type == "error":
        return SSEChunk(
            chunk_type=ChunkType.ERROR,
            data={
                "error": {
                    "message": event.get("message", "Unknown error"),
                    "type": event.get("error_code", "runtime_error"),
                }
            },
        )
    elif event_type == "done":
        return SSEChunk(
            chunk_type=ChunkType.DONE,
            data={},
        )
    else:
        # 默认为内容 chunk
        return SSEChunk(
            chunk_type=ChunkType.CONTENT,
            data={
                "id": event.get("id", "chatcmpl-xxx"),
                "object": "chat.completion.chunk",
                "created": event.get("created", 0),
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": event.get("content", ""),
                        },
                        "finish_reason": None,
                    }
                ],
            },
        )


def _format_sse_chunk(chunk: SSEChunk) -> str:
    """格式化 SSE chunk。"""
    if chunk.chunk_type == ChunkType.DONE:
        return "data: [DONE]\n\n"

    import json
    return f"data: {json.dumps(chunk.data)}\n\n"


def encode_mid_stream_error(error_message: str, error_code: str = "mid_stream_error") -> str:
    """编码 mid-stream error 为 SSE chunk。

    对齐: agent-backend-system.md §8.2 mid-stream error 编码

    Args:
        error_message: 错误消息
        error_code: 错误码

    Returns:
        SSE 格式的错误 chunk
    """
    error_data = {
        "error": {
            "message": error_message,
            "type": error_code,
        }
    }
    import json
    return f"data: {json.dumps(error_data)}\n\n"
