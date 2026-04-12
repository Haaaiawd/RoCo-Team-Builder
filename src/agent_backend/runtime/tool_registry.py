"""
工具注册表 — 为 Agent 提供资料查询与卡片渲染工具。

职责：
- 注册 get_spirit_profile 工具：查询资料 + 渲染卡片组合
- 注册 search_spirits 工具：搜索精灵候选列表
- 工具失败时返回降级信息，不泄漏内部异常堆栈

对齐: agent-backend-system.md §4.2 Tool Registry、§5.1 工具调用流程
验收标准: T3.2.2 工具结果回传输出 html/fallback_text/render_mode/metadata
"""

from __future__ import annotations

from typing import Protocol

from ..integrations.data_layer_client import IDataLayerClient
from ..integrations.spirit_card_client import ISpiritCardClient


class IToolRegistry(Protocol):
    """工具注册表协议 — 提供可被 Agent 调用的工具函数。"""

    def get_spirit_profile(self, spirit_name: str) -> dict:
        """获取精灵资料并渲染卡片（组合工具）。"""
        ...

    def search_spirits(self, query: str, limit: int = 5) -> dict:
        """搜索精灵候选列表。"""
        ...


class ToolRegistry:
    """工具注册表 — 组合 data-layer 与 spirit-card 能力。"""

    def __init__(
        self,
        data_client: IDataLayerClient,
        card_client: ISpiritCardClient,
    ) -> None:
        self._data_client = data_client
        self._card_client = card_client

    async def get_spirit_profile(self, spirit_name: str) -> dict:
        """获取精灵资料并渲染卡片（组合工具）。

        流程:
        1. 调用 data_layer.get_spirit_info 获取结构化资料
        2. 若成功，调用 spirit_card.render_spirit_card 渲染卡片
        3. 若任一步骤失败，返回带降级信息的工具结果

        Returns:
            {
                "success": bool,
                "spirit_profile": dict | None,
                "card_html": str | None,
                "card_fallback_text": str,
                "card_render_mode": str,
                "card_metadata": dict,
                "wiki_url": str | None,
                "error_message": str | None,
            }
        """
        # Step 1: 查询资料
        data_result = await self._data_client.get_spirit_info(spirit_name)

        if not data_result["success"]:
            # 资料查询失败，直接返回降级信息
            return {
                "success": False,
                "spirit_profile": None,
                "card_html": None,
                "card_fallback_text": f"未找到 '{spirit_name}' 的资料",
                "card_render_mode": "text_only",
                "card_metadata": {},
                "wiki_url": data_result.get("wiki_url"),
                "error_message": data_result["error_message"],
            }

        profile = data_result["spirit_profile"]

        # Step 2: 渲染卡片
        card_result = await self._card_client.render_spirit_card(profile)

        return {
            "success": card_result["success"],
            "spirit_profile": profile,
            "card_html": card_result.get("html"),
            "card_fallback_text": card_result.get("fallback_text", f"{profile.get('display_name', spirit_name)}"),
            "card_render_mode": card_result.get("render_mode", "text_only"),
            "card_metadata": card_result.get("metadata", {}),
            "wiki_url": data_result.get("wiki_url"),
            "error_message": card_result.get("error_message"),
        }

    async def search_spirits(self, query: str, limit: int = 5) -> dict:
        """搜索精灵候选列表。

        Returns:
            {
                "success": bool,
                "candidates": list[dict],
                "error_message": str | None,
            }
        """
        try:
            candidates = await self._data_client.search_wiki(query, limit=limit)
            return {
                "success": True,
                "candidates": candidates,
                "error_message": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "candidates": [],
                "error_message": "搜索失败",
            }
