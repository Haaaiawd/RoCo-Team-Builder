"""
data-layer-system 缓存注册中心

实现 ADR-002: cachetools 内存 TTL Cache。
配置约束对齐: data-layer-system.md §7.1 关键配置约束。

缓存键由 key_builder (T1.2.1) 生成，本模块只负责缓存实例的
创建、配置和统一访问点。
"""

from __future__ import annotations

from cachetools import TTLCache


# ---------------------------------------------------------------------------
# ADR-002 配置常量 (data-layer-system.md §7.1)
# ---------------------------------------------------------------------------

SPIRIT_PROFILE_TTL_SECONDS: int = 3600   # 精灵详情 1 小时
SEARCH_RESULT_TTL_SECONDS: int = 600     # 搜索结果 10 分钟
CACHE_MAX_ENTRIES: int = 500             # 最大缓存条目


# ---------------------------------------------------------------------------
# Cache instances
# ---------------------------------------------------------------------------


class CacheRegistry:
    """统一缓存注册中心 — 管理各类数据的 TTL 缓存实例。"""

    def __init__(self) -> None:
        self.spirit_profiles: TTLCache = TTLCache(
            maxsize=CACHE_MAX_ENTRIES,
            ttl=SPIRIT_PROFILE_TTL_SECONDS,
        )
        self.search_results: TTLCache = TTLCache(
            maxsize=CACHE_MAX_ENTRIES,
            ttl=SEARCH_RESULT_TTL_SECONDS,
        )

    def clear_all(self) -> None:
        """清空所有缓存 — 用于测试或热重载。"""
        self.spirit_profiles.clear()
        self.search_results.clear()
