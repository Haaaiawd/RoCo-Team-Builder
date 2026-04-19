"""
别名索引 — 管理精灵名称的规范名与别名映射。

对齐: data-layer-system.md §4.2 Alias Index
     data-layer-system.detail.md §3.1 resolve_spirit_name 伪代码
"""

from __future__ import annotations


class AliasIndex:
    """精灵别名索引 — 提供规范名查找和别名到规范名的映射。

    canonical_index: {规范名小写 -> 规范名原始形式}
    alias_map: {别名小写 -> 规范名原始形式}

    v2 初期别名表不完整，模糊匹配作为兜底。
    """

    def __init__(self) -> None:
        self._canonical_index: dict[str, str] = {}
        self._alias_map: dict[str, str] = {}

    def register_canonical(self, canonical_name: str) -> None:
        """注册一个规范名。"""
        self._canonical_index[canonical_name.strip().lower()] = canonical_name

    def register_alias(self, alias: str, canonical_name: str) -> None:
        """注册一个别名到规范名的映射。"""
        self._alias_map[alias.strip().lower()] = canonical_name

    def lookup_canonical(self, query: str) -> str | None:
        """查找规范名精确命中。"""
        return self._canonical_index.get(query.strip().lower())

    def lookup_alias(self, query: str) -> str | None:
        """查找别名精确命中，返回对应规范名。"""
        return self._alias_map.get(query.strip().lower())

    @property
    def canonical_names(self) -> list[str]:
        """返回所有已注册的规范名列表。"""
        return list(self._canonical_index.values())

    def load_aliases(self, alias_dict: dict[str, list[str]]) -> None:
        """批量加载别名表。

        Args:
            alias_dict: {规范名: [别名1, 别名2, ...]}
        """
        for canonical_name, aliases in alias_dict.items():
            self.register_canonical(canonical_name)
            for alias in aliases:
                self.register_alias(alias, canonical_name)
