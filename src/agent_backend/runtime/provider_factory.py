"""
Provider 工厂 — 从环境变量构建 OpenAIProvider + RunConfig。

职责：
- 读取 ROCO_PROVIDER_MODEL / ROCO_PROVIDER_BASE_URL / ROCO_PROVIDER_API_KEY
- 构建 OpenAIProvider(use_responses=False) 实例
- 生成 RunConfig 供 Runner.run_streamed 使用
- 支持 OpenRouter 等任意 OpenAI 兼容端点

对齐: agent-backend-system.md §7 技术选型
     agent-backend-system.detail.md §3.5 run_agent_turn
     ADR-001: OpenAI Agents SDK + OpenRouter BYOK

SDK 用法: OpenAIProvider 是 ModelProvider 实现，通过 RunConfig.model_provider 注入 Runner。
use_responses=False 确保 SDK 使用 Chat Completions API 而非 Responses API。
"""

from __future__ import annotations

import os
from typing import Any

from ..app.model_catalog import ModelCatalogEntry

try:
    from agents import OpenAIProvider, RunConfig
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    OpenAIProvider = None  # type: ignore
    RunConfig = None  # type: ignore


# 环境变量键名
ENV_PROVIDER_MODEL = "ROCO_PROVIDER_MODEL"
ENV_PROVIDER_BASE_URL = "ROCO_PROVIDER_BASE_URL"
ENV_PROVIDER_API_KEY = "ROCO_PROVIDER_API_KEY"

# 默认值
DEFAULT_PROVIDER_MODEL = "gpt-4o"
DEFAULT_PROVIDER_BASE_URL = "https://openrouter.ai/api/v1"


class ProviderConfigError(Exception):
    """Provider 配置错误 — API Key 缺失等。"""


def build_provider_for_model(model_entry: ModelCatalogEntry) -> Any:
    """按模型目录条目构建 OpenAIProvider。"""
    api_key = os.environ.get(ENV_PROVIDER_API_KEY, "")

    if not api_key:
        raise ProviderConfigError(
            f"环境变量 {ENV_PROVIDER_API_KEY} 未设置。"
            "请在 .env 文件或容器环境中配置 LLM Provider API Key。"
        )

    if not AGENTS_AVAILABLE:
        raise RuntimeError(
            "openai-agents package not installed. "
            "Install with: pip install openai-agents"
        )

    return OpenAIProvider(
        api_key=api_key,
        base_url=model_entry.provider_base_url,
        use_responses=False,
    )


def build_run_config_for_model(model_entry: ModelCatalogEntry) -> Any:
    """按模型目录条目构建 RunConfig。"""
    provider = build_provider_for_model(model_entry)
    return RunConfig(
        model=model_entry.provider_model_name,
        model_provider=provider,
    )


def build_run_config() -> Any:
    """从环境变量构建 RunConfig（含 OpenAIProvider + model 名称）。

    Returns:
        RunConfig 实例，可直接传给 Runner.run_streamed(run_config=...)

    Raises:
        ProviderConfigError: API Key 未配置
        RuntimeError: openai-agents 包未安装
    """
    model_name = os.environ.get(ENV_PROVIDER_MODEL, DEFAULT_PROVIDER_MODEL)
    base_url = os.environ.get(ENV_PROVIDER_BASE_URL, DEFAULT_PROVIDER_BASE_URL)
    api_key = os.environ.get(ENV_PROVIDER_API_KEY, "")

    # 先检查 API Key — 这是最常见的配置错误
    if not api_key:
        raise ProviderConfigError(
            f"环境变量 {ENV_PROVIDER_API_KEY} 未设置。"
            "请在 .env 文件或容器环境中配置 LLM Provider API Key。"
        )

    # 再检查 SDK 安装
    if not AGENTS_AVAILABLE:
        raise RuntimeError(
            "openai-agents package not installed. "
            "Install with: pip install openai-agents"
        )

    return build_run_config_for_model(
        ModelCatalogEntry(
            public_model_id="roco-agent",
            provider_model_name=model_name,
            provider_base_url=base_url,
            supports_vision=True,
            enabled=True,
        )
    )
