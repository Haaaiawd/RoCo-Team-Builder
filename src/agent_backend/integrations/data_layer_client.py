"""
Data-Layer 适配器 — 将 DataLayerFacade 包装为 IDataLayerClient 协议。

职责：
- 将 data-layer-system 的异步 Facade 转换为 agent-backend 的同步/异步接口
- 统一错误处理，将 DataLayerError 转为工具降级而非硬失败
- 确保工具调用失败时仍返回带 wiki_url 的降级文本

对齐: agent-backend-system.md §5.2 IDataLayerClient
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from data_layer.app.errors import (
    AmbiguousSpiritNameError,
    DataLayerError,
    SpiritNotFoundError,
    WikiParseError,
    WikiUpstreamTimeoutError,
)
from data_layer.app.facade import DataLayerFacade


class IDataLayerClient(Protocol):
    """数据层客户端协议 — agent-backend 对 data-layer 的抽象接口。"""

    async def get_spirit_info(self, spirit_name: str) -> dict:
        """获取精灵结构化资料（含 BWIKI 链接）。"""
        ...

    async def search_wiki(self, query: str, limit: int = 5) -> list[dict]:
        """搜索精灵候选列表。"""
        ...

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        """属性克制计算。"""
        ...

    async def analyze_team_draft(self, team_draft: dict) -> dict:
        """队伍分析 — 生成 TeamAnalysisSnapshot。"""
        ...


class DataLayerClient:
    """DataLayerFacade 的适配器 — 实现 IDataLayerClient 协议。"""

    def __init__(self, facade: DataLayerFacade) -> None:
        self._facade = facade

    async def get_spirit_info(self, spirit_name: str) -> dict:
        """获取精灵结构化资料。

        失败时仍返回带 wiki_url 的降级信息，不泄漏内部异常堆栈。

        Returns:
            {
                "success": bool,
                "spirit_profile": dict | None,
                "wiki_url": str | None,
                "error_message": str | None,
            }
        """
        try:
            profile = await self._facade.get_spirit_profile(spirit_name)
            profile_dict = asdict(profile)
            return {
                "success": True,
                "spirit_profile": profile_dict,
                "wiki_url": profile_dict.get("wiki_url"),
                "error_message": None,
            }
        except SpiritNotFoundError:
            wiki_link = await self._facade.build_wiki_link(spirit_name)
            return {
                "success": False,
                "spirit_profile": None,
                "wiki_url": wiki_link,
                "error_message": f"未找到精灵 '{spirit_name}'",
            }
        except AmbiguousSpiritNameError as exc:
            candidates = [asdict(c) for c in exc.candidates]
            return {
                "success": False,
                "spirit_profile": None,
                "wiki_url": None,
                "error_message": f"'{spirit_name}' 存在多个候选",
                "candidates": candidates,
            }
        except WikiUpstreamTimeoutError as exc:
            return {
                "success": False,
                "spirit_profile": None,
                "wiki_url": exc.wiki_url,
                "error_message": "BWIKI 请求超时，请稍后重试",
            }
        except WikiParseError as exc:
            return {
                "success": False,
                "spirit_profile": None,
                "wiki_url": exc.wiki_url,
                "error_message": "页面解析失败",
            }
        except DataLayerError:
            return {
                "success": False,
                "spirit_profile": None,
                "wiki_url": None,
                "error_message": "数据查询失败",
            }

    async def search_wiki(self, query: str, limit: int = 5) -> list[dict]:
        """搜索精灵候选列表。

        search_spirits 不抛异常，始终返回候选列表（可能为空）。
        """
        candidates = await self._facade.search_spirits(query, limit=limit)
        return candidates

    async def get_type_matchup(self, type_combo: list[str]) -> dict:
        """属性克制计算 — 纯本地，不依赖网络。"""
        result = await self._facade.get_type_matchup(type_combo)
        return result

    async def analyze_team_draft(self, team_draft: dict) -> dict:
        """队伍分析 — 生成 TeamAnalysisSnapshot。

        失败时返回错误信息，不泄漏内部异常堆栈。

        Returns:
            {
                "success": bool,
                "team_snapshot": dict | None,
                "error_message": str | None,
            }
        """
        try:
            snapshot = await self._facade.analyze_team_draft(team_draft)
            return {
                "success": True,
                "team_snapshot": snapshot,
                "error_message": None,
            }
        except DataLayerError as exc:
            return {
                "success": False,
                "team_snapshot": None,
                "error_message": str(exc),
            }
