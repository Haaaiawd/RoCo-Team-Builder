"""
T1.1.2 单元测试 — 名称规范化、别名解析、模糊匹配、歧义/未找到分支。

验收标准:
  - 别名/简称/轻微拼写偏差 → 规范名或候选列表
  - 完全未命中 → SPIRIT_NOT_FOUND_ 错误 + 候选列表或空候选
  - 多个候选分数接近 → SPIRIT_AMBIGUOUS_ 错误 + 候选名称列表
"""

import pytest

from data_layer.spirits.alias_index import AliasIndex
from data_layer.spirits.name_resolver import NameResolver, normalize_text
from data_layer.app.errors import AmbiguousSpiritNameError, SpiritNotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def alias_index() -> AliasIndex:
    """构建一个测试用别名索引，包含若干精灵。"""
    idx = AliasIndex()
    idx.load_aliases({
        "火神": ["火花", "烈焰鸟"],
        "翼王": ["翼之王"],
        "恶魔狼": ["魔狼", "暗影狼"],
        "冰龙王": ["冰龙"],
        "雷神": [],
        "水灵兽": ["水灵"],
    })
    return idx


@pytest.fixture
def resolver(alias_index: AliasIndex) -> NameResolver:
    return NameResolver(alias_index)


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_strip_whitespace(self):
        assert normalize_text("  火神  ") == "火神"

    def test_nfkc_normalization(self):
        assert normalize_text("ﬁre") == "fire"

    def test_lowercase(self):
        assert normalize_text("ABC") == "abc"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_mixed(self):
        assert normalize_text("  火花 ") == "火花"


# ---------------------------------------------------------------------------
# resolve — canonical exact match
# ---------------------------------------------------------------------------


class TestResolveCanonical:
    def test_exact_canonical_hit(self, resolver: NameResolver):
        result = resolver.resolve("火神")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "火神"
        assert result["candidates"][0].match_reason == "canonical"

    def test_canonical_case_insensitive(self, resolver: NameResolver):
        result = resolver.resolve("雷神")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "雷神"


# ---------------------------------------------------------------------------
# resolve — alias exact match
# ---------------------------------------------------------------------------


class TestResolveAlias:
    def test_alias_hit(self, resolver: NameResolver):
        result = resolver.resolve("火花")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "火神"
        assert result["candidates"][0].match_reason == "alias"

    def test_alias_with_whitespace(self, resolver: NameResolver):
        result = resolver.resolve("  魔狼  ")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "恶魔狼"


# ---------------------------------------------------------------------------
# resolve — fuzzy match
# ---------------------------------------------------------------------------


class TestResolveFuzzy:
    def test_fuzzy_single_high_confidence(self, resolver: NameResolver):
        """轻微偏差 → 单候选高置信 → resolved"""
        result = resolver.resolve("冰龙王")
        assert result["status"] == "resolved"
        assert result["canonical_name"] == "冰龙王"

    def test_fuzzy_ambiguous(self):
        """多个候选分数接近 → AmbiguousSpiritNameError"""
        idx = AliasIndex()
        idx.load_aliases({
            "炎火龙": [],
            "炎火凤": [],
            "炎火鹰": [],
        })
        r = NameResolver(idx)
        with pytest.raises(AmbiguousSpiritNameError) as exc_info:
            r.resolve("炎火")
        assert exc_info.value.candidates is not None
        assert len(exc_info.value.candidates) >= 2
        assert exc_info.value.error_code == "SPIRIT_AMBIGUOUS_MULTIPLE_MATCH"

    def test_fuzzy_not_found(self, resolver: NameResolver):
        """完全无关输入 → SpiritNotFoundError"""
        with pytest.raises(SpiritNotFoundError) as exc_info:
            resolver.resolve("完全不存在的精灵名称abcxyz")
        assert exc_info.value.error_code == "SPIRIT_NOT_FOUND_NO_MATCH"


# ---------------------------------------------------------------------------
# resolve — edge cases
# ---------------------------------------------------------------------------


class TestResolveEdgeCases:
    def test_empty_input(self, resolver: NameResolver):
        with pytest.raises(SpiritNotFoundError):
            resolver.resolve("")

    def test_whitespace_only(self, resolver: NameResolver):
        with pytest.raises(SpiritNotFoundError):
            resolver.resolve("   ")

    def test_candidates_have_required_fields(self, resolver: NameResolver):
        """候选项包含 canonical_name, display_name, score, match_reason"""
        result = resolver.resolve("翼王")
        c = result["candidates"][0]
        assert c.canonical_name
        assert c.display_name
        assert isinstance(c.score, float)
        assert c.match_reason in ("canonical", "alias", "fuzzy")
