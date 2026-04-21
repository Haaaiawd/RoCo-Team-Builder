from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from data_layer.app.facade import DataLayerFacade
from data_layer.cache.registry import CacheRegistry
from data_layer.spirits.alias_index import AliasIndex
from data_layer.spirits.local_dex import load_local_aliases
from data_layer.spirits.name_resolver import NameResolver
from data_layer.spirits.repository import SpiritRepository
from data_layer.wiki.gateway import WikiGateway
from data_layer.wiki.parser import WikiParser


@pytest.mark.asyncio
async def test_default_facade_searches_local_spirit_alias_index() -> None:
    facade = DataLayerFacade()
    result = await facade.search_spirits("彩蝶鲨", limit=5)

    assert result
    assert result[0]["canonical_name"] == "彩蝶鲨"


@pytest.mark.asyncio
async def test_repository_returns_local_profile_without_wiki_call() -> None:
    alias_index = AliasIndex()
    alias_index.load_aliases(load_local_aliases())
    resolver = NameResolver(alias_index)

    gateway = WikiGateway()
    gateway.fetch_spirit_page = AsyncMock(side_effect=AssertionError("should not call wiki"))
    repository = SpiritRepository(
        resolver,
        gateway,
        WikiParser(),
        CacheRegistry(),
    )

    profile = await repository.get_spirit_profile("圆号鱼")
    assert profile.canonical_name == "圆号鱼"
    assert "水" in profile.types
    assert any(skill.get("name") == "湿润印记" for skill in profile.skills)
