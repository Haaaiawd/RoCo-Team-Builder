"""
Wiki Parser — 将 MediaWiki API 原始响应转为领域字段。

避免上游绑定页面结构。解析器从 wikitext 中提取结构化精灵字段。
对齐: data-layer-system.md §4.2 Wiki Parser
     data-layer-system.detail.md §2 SpiritProfile / §5.1 页面模板漂移

注意: v2 初期解析器基于 BWIKI 精灵页面的 wikitext 模板格式实现。
     实际模板字段需对真实样本微调。当前实现为合理骨架 + 最小字段校验。
"""

from __future__ import annotations

import re

from ..app.contracts import SpiritProfile
from ..app.errors import WikiParseError


class WikiParser:
    """将 MediaWiki action=parse 返回的 wikitext 解析为 SpiritProfile。"""

    def parse_spirit_profile(self, raw_payload: dict, wiki_url: str) -> SpiritProfile:
        """解析精灵页面 wikitext 为 SpiritProfile。

        Args:
            raw_payload: MediaWiki API JSON 响应
            wiki_url: 精灵 BWIKI 页面链接

        Returns:
            SpiritProfile 领域对象

        Raises:
            WikiParseError: 解析失败或缺少必要字段
        """
        try:
            parse_block = raw_payload.get("parse", {})
            page_title = parse_block.get("title", "")
            wikitext_block = parse_block.get("wikitext", {})
            wikitext = wikitext_block.get("*", "") if isinstance(wikitext_block, dict) else ""

            if not wikitext:
                raise WikiParseError(
                    f"wikitext 为空: {page_title}",
                    wiki_url=wiki_url,
                )

            display_name = page_title or ""
            canonical_name = display_name
            types = self._extract_types(wikitext)
            base_stats = self._extract_base_stats(wikitext)
            skills = self._extract_skills(wikitext)
            bloodline_type = self._extract_bloodline(wikitext)
            evolution_chain = self._extract_evolution_chain(wikitext)

            profile = SpiritProfile(
                canonical_name=canonical_name,
                display_name=display_name,
                types=types,
                base_stats=base_stats,
                skills=skills,
                bloodline_type=bloodline_type,
                evolution_chain=evolution_chain,
                wiki_url=wiki_url,
            )

            if not profile.display_name or not profile.wiki_url:
                raise WikiParseError(
                    f"profile 缺少必要字段 (display_name/wiki_url): {page_title}",
                    wiki_url=wiki_url,
                )

            return profile

        except WikiParseError:
            raise
        except Exception as exc:
            raise WikiParseError(
                f"解析精灵页面失败: {exc}",
                wiki_url=wiki_url,
            ) from exc

    # ------------------------------------------------------------------
    # 字段提取方法 — 从 wikitext 模板中抽取结构化数据
    # 具体正则需对 BWIKI 真实样本微调
    # ------------------------------------------------------------------

    def _extract_types(self, wikitext: str) -> list[str]:
        """提取精灵系别。"""
        match = re.search(r"\|系别\s*=\s*(.+)", wikitext)
        if match:
            raw = match.group(1).strip()
            return [t.strip() for t in re.split(r"[/、,]", raw) if t.strip()]
        return []

    def _extract_base_stats(self, wikitext: str) -> dict[str, int]:
        """提取种族值六维数据。"""
        stat_keys = {
            "精力": "hp",
            "攻击": "attack",
            "防御": "defense",
            "魔攻": "magic_attack",
            "魔抗": "magic_defense",
            "速度": "speed",
        }
        stats: dict[str, int] = {}
        for cn_key, en_key in stat_keys.items():
            match = re.search(rf"\|{cn_key}\s*=\s*(\d+)", wikitext)
            if match:
                stats[en_key] = int(match.group(1))
        return stats

    def _extract_skills(self, wikitext: str) -> list[dict]:
        """提取技能列表 — 骨架实现，需对真实模板微调。"""
        skills: list[dict] = []
        skill_pattern = re.finditer(
            r"\|技能名(\d*)\s*=\s*(.+?)(?:\n|\|)",
            wikitext,
        )
        for match in skill_pattern:
            skill_name = match.group(2).strip()
            if skill_name:
                skills.append({"name": skill_name})
        return skills

    def _extract_bloodline(self, wikitext: str) -> str | None:
        """提取血脉类型。"""
        match = re.search(r"\|血脉\s*=\s*(.+)", wikitext)
        if match:
            return match.group(1).strip() or None
        return None

    def _extract_evolution_chain(self, wikitext: str) -> list[dict]:
        """提取进化链 — 骨架实现，需对真实模板微调。"""
        chain: list[dict] = []
        evo_pattern = re.finditer(
            r"\|进化(\d*)\s*=\s*(.+?)(?:\n|\|)",
            wikitext,
        )
        for match in evo_pattern:
            stage = match.group(2).strip()
            if stage:
                chain.append({"stage_name": stage, "condition": None})
        return chain
