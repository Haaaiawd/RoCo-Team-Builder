"""
Chat Runtime — 把 ChatRequestContext 接到 openai-agents Runner 的薄适配层。

职责：
- 从 AgentFactory 取 Agent 实例
- 把 ChatRequestContext.messages 转成 Runner 可消费的输入
- 提供 `run_nonstream` 返回 OpenAI 兼容 JSON
- 提供 `stream` 产出 OpenAI 兼容的 SSE chunk（增量 delta + [DONE] + mid-stream error）

对齐:
- agent-backend-system.md §4.2 OpenAI Compatibility Router
- agent-backend-system.md §5.1 stream_runtime_events
- agent-backend-system.md §8.2 SSE 格式 / mid-stream error 编码

设计约束：
- 定义 `IChatRuntime` 协议，允许路由层注入假实现（测试）/ 真实实现（生产）。
- 真实 Runner 调用失败时不要把裸异常泄漏到 HTTP 层 —— 非流式走 500 JSON，
  流式走 mid-stream error chunk + [DONE]，保持 OpenAI 协议不断流。
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol

from ..app.request_context import ChatRequestContext
from ..app.session_service import SessionRecord
from .agent_factory import AGENTS_AVAILABLE, IAgentFactory

try:
    from agents import Runner
    RUNNER_AVAILABLE = True
except ImportError:
    RUNNER_AVAILABLE = False
    Runner = None  # type: ignore


class IChatRuntime(Protocol):
    """Chat Runtime 协议 —— 供路由层按请求分发。"""

    async def run_nonstream(
        self,
        context: ChatRequestContext,
        session_record: SessionRecord,
    ) -> dict[str, Any]:
        """同步聊天 —— 返回 OpenAI Chat Completions 兼容 JSON。"""
        ...

    def stream(
        self,
        context: ChatRequestContext,
        session_record: SessionRecord,
    ) -> AsyncIterator[str]:
        """流式聊天 —— 产出 OpenAI Chat Completions 兼容 SSE chunk。"""
        ...


@dataclass
class RuntimeConfig:
    """Runtime 的可调参数。"""

    max_turns: int = 10


def _extract_latest_user_text(context: ChatRequestContext) -> str:
    """从 ChatRequestContext 中提取最后一条 user 消息的文本。

    支持 OpenAI content 两种形态：
    - str：直接返回。
    - list[part]：拼接 type == 'text' 的片段；image_url 片段由上游的
      CAPABILITY_ 守卫过滤，这里忽略。
    """
    for message in reversed(context.messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts: list[str] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text":
                    texts.append(str(part.get("text", "")))
            if texts:
                return "\n".join(texts)
    return ""


def _build_chat_completion_envelope(
    content: str,
    model_id: str,
    request_id: str,
    finish_reason: str = "stop",
) -> dict[str, Any]:
    """构造 OpenAI Chat Completions 非流式响应 JSON。"""
    return {
        "id": f"chatcmpl_{request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def _build_delta_chunk(
    delta: str,
    model_id: str,
    request_id: str,
    finish_reason: str | None = None,
) -> str:
    """构造 OpenAI Chat Completions 流式 chunk（delta）。"""
    payload = {
        "id": f"chatcmpl_{request_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "delta": {"content": delta} if delta else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _build_error_chunk(message: str, code: str) -> str:
    """构造 mid-stream error chunk。"""
    payload = {
        "error": {
            "message": message,
            "type": code,
        }
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


DONE_SENTINEL = "data: [DONE]\n\n"


class AgentChatRuntime:
    """真实 Chat Runtime —— 调用 `openai-agents` Runner。"""

    def __init__(
        self,
        agent_factory: IAgentFactory,
        config: RuntimeConfig | None = None,
    ) -> None:
        if not AGENTS_AVAILABLE or not RUNNER_AVAILABLE:
            raise RuntimeError(
                "openai-agents package not installed; "
                "cannot construct AgentChatRuntime."
            )
        self._agent_factory = agent_factory
        self._config = config or RuntimeConfig()

    async def run_nonstream(
        self,
        context: ChatRequestContext,
        session_record: SessionRecord,
    ) -> dict[str, Any]:
        agent = self._agent_factory.create_team_builder_agent()
        user_input = _extract_latest_user_text(context)
        result = await Runner.run(
            agent,
            user_input,
            max_turns=self._config.max_turns,
        )
        final_output = getattr(result, "final_output", None) or ""
        session_record.add_item({
            "role": "assistant",
            "content": str(final_output),
        })
        return _build_chat_completion_envelope(
            content=str(final_output),
            model_id=context.model_entry.public_model_id,
            request_id=context.request_id,
        )

    async def stream(
        self,
        context: ChatRequestContext,
        session_record: SessionRecord,
    ) -> AsyncIterator[str]:
        async def _iter() -> AsyncIterator[str]:
            agent = self._agent_factory.create_team_builder_agent()
            user_input = _extract_latest_user_text(context)
            model_id = context.model_entry.public_model_id
            request_id = context.request_id
            aggregated: list[str] = []
            try:
                result = Runner.run_streamed(
                    agent,
                    user_input,
                    max_turns=self._config.max_turns,
                )
                async for event in result.stream_events():
                    delta = _extract_delta_from_stream_event(event)
                    if delta:
                        aggregated.append(delta)
                        yield _build_delta_chunk(delta, model_id, request_id)
                yield _build_delta_chunk("", model_id, request_id, finish_reason="stop")
            except Exception as exc:  # noqa: BLE001 — intentionally broad; we must never bubble to HTTP
                yield _build_error_chunk(str(exc), "runtime_error")
            finally:
                if aggregated:
                    session_record.add_item({
                        "role": "assistant",
                        "content": "".join(aggregated),
                    })
                yield DONE_SENTINEL

        return _iter()


def _extract_delta_from_stream_event(event: Any) -> str:
    """从 Runner.stream_events() 事件里解出文本 delta。

    使用 duck typing 而不是 isinstance —— openai-agents 在 0.0.5 与 0.14.x
    之间事件类型有过变化，用属性探测更稳。
    """
    if getattr(event, "type", None) != "raw_response_event":
        return ""
    data = getattr(event, "data", None)
    if data is None:
        return ""
    data_type = getattr(data, "type", "") or ""
    if "text.delta" not in str(data_type):
        return ""
    delta = getattr(data, "delta", None)
    if isinstance(delta, str):
        return delta
    if delta is None:
        return ""
    text = getattr(delta, "text", None)
    if isinstance(text, str):
        return text
    return str(delta)


def new_request_id() -> str:
    """生成新的 request_id（用于非 context 直接触发的调用，如测试）。"""
    return f"req_{uuid.uuid4().hex}"
