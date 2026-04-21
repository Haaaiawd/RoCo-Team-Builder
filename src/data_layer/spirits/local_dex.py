"""
本地精灵图鉴加载器 — 为离线/弱网场景提供最小可用资料兜底。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..app.contracts import SpiritProfile
from ..wiki.endpoint_builder import build_wiki_link

_DEFAULT_SPIRIT_DATA_PATH = Path(__file__).parent.parent / "static" / "data" / "spirits.json"


def load_local_spirit_profiles(
    data_path: Path | None = None,
) -> dict[str, SpiritProfile]:
    """加载本地精灵资料，返回 canonical_name -> SpiritProfile。"""
    path = data_path or _DEFAULT_SPIRIT_DATA_PATH
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    result: dict[str, SpiritProfile] = {}
    for item in data.get("spirits", []):
        canonical_name = str(item.get("canonical_name", "")).strip()
        if not canonical_name:
            continue

        skills = [{"name": skill} for skill in item.get("skills", []) if str(skill).strip()]
        profile = SpiritProfile(
            canonical_name=canonical_name,
            display_name=str(item.get("display_name", canonical_name)).strip() or canonical_name,
            types=[str(t).strip() for t in item.get("types", []) if str(t).strip()],
            base_stats={
                str(k): int(v)
                for k, v in dict(item.get("base_stats", {})).items()
                if str(k).strip()
            },
            skills=skills,
            bloodline_type=item.get("bloodline_type"),
            evolution_chain=[
                evo
                for evo in item.get("evolution_chain", [])
                if isinstance(evo, dict)
            ],
            wiki_url=str(item.get("wiki_url", "")).strip() or build_wiki_link(canonical_name),
        )
        result[canonical_name] = profile

    return result


def load_local_aliases(data_path: Path | None = None) -> dict[str, list[str]]:
    """加载本地图鉴中的别名映射，返回 {canonical_name: aliases[]}。"""
    path = data_path or _DEFAULT_SPIRIT_DATA_PATH
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    alias_map: dict[str, list[str]] = {}
    for item in data.get("spirits", []):
        canonical_name = str(item.get("canonical_name", "")).strip()
        if not canonical_name:
            continue
        aliases = [str(a).strip() for a in item.get("aliases", []) if str(a).strip()]
        alias_map[canonical_name] = aliases

    return alias_map
