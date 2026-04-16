"""
Agent Runtime 服务 — 编排 session/quota/agent/stream 完整请求路径。

职责：
- 将归一化后的 ChatRequestContext 转换为 Agent 输入
- 调用 Runner.run_streamed 驱动 Agent 推理循环
- 将 SDK StreamEvent 转换为 OpenAI SSE chunk
- 处理 mid-stream error 与 [DONE] 收尾

对齐: agent-backend-system.md §4.1 数据流、§5.1 run_agent_turn / stream_runtime_events
     agent-backend-system.detail.md §3.5 run_agent_turn、§4.1 请求处理路径选择
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator

try:
    from agents import Runner
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

from ..app.request_context import ChatRequestContext
from ..app.session_service import SessionRecord
from ..app.stream_bridge import encode_mid_stream_error
from .agent_factory import AgentFactory
from .provider_factory import build_run_config_for_model


def _make_completion_id() -> str:
    """生成 OpenAI 兼容的 completion ID。"""
    return f"chatcmpl-{uuid.uuid4().hex[:29]}"


def _messages_to_input(messages: list[dict[str, Any]], session_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将请求 messages + session 历史合并为 Agent 输入。

    对齐: agent-backend-system.detail.md §3.5 — 历史消息与本轮输入的拼接顺序必须稳定
    """
    # session_items 是之前的对话历史，messages 是本轮输入
    # 拼接顺序: 历史 → 本轮
    input_items: list[dict[str, Any]] = []
    for item in session_items:
        input_items.append(item)
    for msg in messages:
        input_items.append(msg)
    return input_items


def _get_owned_spirits(session: SessionRecord) -> list[str]:
    """从 session 中提取 owned_spirits 约束。

    对齐: agent-backend-system.detail.md §3.7 owned_spirits 约束
    """
    # 支持 SessionRecordExtended 子类
    if hasattr(session, "get_owned_spirits") and hasattr(session, "has_owned_spirits"):
        if session.has_owned_spirits():
            return session.get_owned_spirits()
    return []


def run_agent_turn(
    context: ChatRequestContext,
    session_items: list[dict[str, Any]],
    agent_factory: AgentFactory,
    owned_spirits: list[str] | None = None,
) -> Any:
    """执行单次 Agent runtime，返回 SDK streaming result。"""
    agent_input = _messages_to_input(context.messages, session_items)

    if owned_spirits:
        agent_factory.set_owned_spirits(owned_spirits)

    agent = agent_factory.create_team_builder_agent()
    run_config = build_run_config_for_model(context.model_entry)

    return Runner.run_streamed(
        starting_agent=agent,
        input=agent_input,
        run_config=run_config,
    )


async def run_agent_streamed(
    context: ChatRequestContext,
    session: SessionRecord,
    agent_factory: AgentFactory,
) -> AsyncIterator[str]:
    """执行 Agent 推理并以 SSE chunk 形式流式输出。

    对齐: agent-backend-system.md §5.1 run_agent_turn + stream_runtime_events
         agent-backend-system.detail.md §3.5, §4.1

    Args:
        context: 归一化后的请求上下文
        session: 当前会话记录（含历史消息和 owned_spirits）
        agent_factory: Agent 工厂实例

    Yields:
        OpenAI 兼容的 SSE chunk 字符串
    """
    if not AGENTS_AVAILABLE:
        yield encode_mid_stream_error(
            "Agent Runtime 不可用：openai-agents 包未安装",
            error_code="RUNTIME_UNAVAILABLE",
        )
        yield "data: [DONE]\n\n"
        return

    chunk_id = _make_completion_id()
    model_id = context.model_entry.public_model_id

    # 创建 Agent
    try:
        owned_spirits = _get_owned_spirits(session)
        result = run_agent_turn(
            context,
            session.items,
            agent_factory,
            owned_spirits=owned_spirits,
        )
    except Exception as exc:
        yield encode_mid_stream_error(
            f"Agent 创建失败: {exc}",
            error_code="AGENT_CREATION_ERROR",
        )
        yield "data: [DONE]\n\n"
        return

    try:
        # 将 SDK StreamEvent 转换为 OpenAI SSE chunk
        async for event in result.stream_events():
            sse_chunks = _convert_stream_event(event, chunk_id, model_id)
            for chunk in sse_chunks:
                yield chunk

        # 将本轮对话写入 session 历史
        if result.final_output:
            session.add_item({
                "role": "assistant",
                "content": result.final_output if isinstance(result.final_output, str) else str(result.final_output),
            })

        yield "data: [DONE]\n\n"

    except Exception as exc:
        yield encode_mid_stream_error(
            f"Agent 推理异常: {exc}",
            error_code="RUNTIME_ERROR",
        )
        yield "data: [DONE]\n\n"


def _convert_stream_event(event: Any, chunk_id: str, model_id: str) -> list[str]:
    """将单个 SDK StreamEvent 转换为 SSE chunk 列表。

    对齐: agent-backend-system.md §5.1 stream_runtime_events
         agent-backend-system.detail.md §3.3

    SDK StreamEvent 类型:
    - RawResponsesStreamEvent: LLM 原始 token 输出
    - RunItemStreamEvent: 工具调用/输出/消息等语义事件
    - AgentUpdatedStreamEvent: Agent 切换
    """
    chunks: list[str] = []
    event_type = getattr(event, "type", None)

    if event_type == "raw_response_event":
        # LLM 原始响应事件 — 提取 text delta
        data = getattr(event, "data", None)
        if data is None:
            return chunks

        # 从 Response API 事件中提取文本增量
        delta_text = _extract_text_delta(data)
        if delta_text:
            chunk_data = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": delta_text},
                        "finish_reason": None,
                    }
                ],
            }
            chunks.append(f"data: {json.dumps(chunk_data)}\n\n")

    elif event_type == "run_item_stream_event":
        # 语义事件 — 工具调用/输出/消息
        name = getattr(event, "name", "")
        item = getattr(event, "item", None)

        if name == "message_output_created" and item is not None:
            # Agent 最终文本输出
            content = _extract_item_content(item)
            if content:
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_id,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": "stop",
                        }
                    ],
                }
                chunks.append(f"data: {json.dumps(chunk_data)}\n\n")

        elif name == "tool_called" and item is not None:
            # 工具调用 — 在 SSE 中以 function 字段传递
            tool_name = getattr(getattr(item, "raw_item", None), "name", "unknown")
            tool_args = getattr(getattr(item, "raw_item", None), "arguments", "{}")
            chunk_data = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": None,
                            "function_call": {
                                "name": tool_name,
                                "arguments": tool_args if isinstance(tool_args, str) else json.dumps(tool_args),
                            },
                        },
                        "finish_reason": None,
                    }
                ],
            }
            chunks.append(f"data: {json.dumps(chunk_data)}\n\n")

        elif name == "tool_output" and item is not None:
            # 工具输出 — 作为 assistant 消息的一部分
            output = getattr(item, "output", "")
            if output:
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_id,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": f"\n[工具结果] {output}\n"},
                            "finish_reason": None,
                        }
                    ],
                }
                chunks.append(f"data: {json.dumps(chunk_data)}\n\n")

    elif event_type == "agent_updated_stream_event":
        # Agent 切换 — 不需要特殊 SSE 处理
        pass

    return chunks


def _extract_text_delta(data: Any) -> str:
    """从 Response API 事件中提取文本增量。"""
    # ResponseTextDeltaEvent
    if hasattr(data, "delta"):
        delta = data.delta
        if isinstance(delta, str):
            return delta
    # ResponseOutputTextDeltaEvent
    if hasattr(data, "part") and hasattr(data.part, "text"):
        return data.part.text or ""
    return ""


def _extract_item_content(item: Any) -> str:
    """从 RunItem 中提取文本内容。"""
    # MessageOutputItem
    if hasattr(item, "raw_item"):
        raw = item.raw_item
        if hasattr(raw, "content"):
            content = raw.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text", "")
                        if text:
                            texts.append(text)
                    elif hasattr(part, "text"):
                        texts.append(part.text or "")
                return "".join(texts)
    # 直接有 content 属性
    if hasattr(item, "content"):
        content = item.content
        if isinstance(content, str):
            return content
    return ""
