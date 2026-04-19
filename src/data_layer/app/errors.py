"""
data-layer-system 结构化错误定义

错误码前缀对齐 02_ARCHITECTURE_OVERVIEW.md §3.5 跨系统错误分类矩阵。
所有错误均可被 agent-backend-system 捕获并转为终端用户可读的 OpenAI 风格错误。
"""

from __future__ import annotations

from .contracts import SearchCandidate


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class DataLayerError(Exception):
    """数据层错误基类 — 所有数据层异常必须继承此类。"""

    error_code: str = "DATA_LAYER_UNKNOWN"
    retryable: bool = False
    wiki_url: str = ""

    def __init__(self, message: str, *, wiki_url: str = "", retryable: bool | None = None):
        super().__init__(message)
        self.message = message
        if wiki_url:
            self.wiki_url = wiki_url
        if retryable is not None:
            self.retryable = retryable


# ---------------------------------------------------------------------------
# SPIRIT_NOT_FOUND_
# ---------------------------------------------------------------------------


class SpiritNotFoundError(DataLayerError):
    """精灵未找到 — 名称无法解析为任何已知实体。"""

    error_code: str = "SPIRIT_NOT_FOUND_NO_MATCH"

    def __init__(
        self,
        message: str,
        *,
        wiki_url: str = "",
        candidates: list[SearchCandidate] | None = None,
    ):
        super().__init__(message, wiki_url=wiki_url)
        self.candidates = candidates


# ---------------------------------------------------------------------------
# SPIRIT_AMBIGUOUS_
# ---------------------------------------------------------------------------


class AmbiguousSpiritNameError(DataLayerError):
    """精灵名歧义 — 多个候选分数接近，需用户确认。"""

    error_code: str = "SPIRIT_AMBIGUOUS_MULTIPLE_MATCH"

    def __init__(
        self,
        message: str,
        *,
        wiki_url: str = "",
        candidates: list[SearchCandidate] | None = None,
    ):
        super().__init__(message, wiki_url=wiki_url)
        self.candidates = candidates or []


# ---------------------------------------------------------------------------
# WIKI_TIMEOUT_
# ---------------------------------------------------------------------------


class WikiUpstreamTimeoutError(DataLayerError):
    """BWIKI 超时 — 上游请求超出 5s 边界。"""

    error_code: str = "WIKI_TIMEOUT_UPSTREAM"
    retryable: bool = True

    def __init__(self, message: str, *, wiki_url: str = ""):
        super().__init__(message, wiki_url=wiki_url, retryable=True)


# ---------------------------------------------------------------------------
# WIKI_PARSE_
# ---------------------------------------------------------------------------


class WikiParseError(DataLayerError):
    """BWIKI 解析失败 — 页面结构无法转为领域对象。"""

    error_code: str = "WIKI_PARSE_FAILED"
    retryable: bool = False

    def __init__(self, message: str, *, wiki_url: str = ""):
        super().__init__(message, wiki_url=wiki_url, retryable=False)


# ---------------------------------------------------------------------------
# SEARCH_
# ---------------------------------------------------------------------------


class SearchUnavailableError(DataLayerError):
    """搜索功能不可用。"""

    error_code: str = "SEARCH_UNAVAILABLE"
    retryable: bool = True


# ---------------------------------------------------------------------------
# STATIC_
# ---------------------------------------------------------------------------


class InvalidTypeComboError(DataLayerError):
    """非法属性组合。"""

    error_code: str = "STATIC_INVALID_TYPE_COMBO"
    retryable: bool = False


class KnowledgeTopicNotFoundError(DataLayerError):
    """未知知识主题 key。"""

    error_code: str = "STATIC_TOPIC_NOT_FOUND"
    retryable: bool = False


# ---------------------------------------------------------------------------
# TEAM_ANALYSIS_
# ---------------------------------------------------------------------------


class TeamAnalysisInputError(DataLayerError):
    """队伍分析输入错误 — TeamDraft 字段缺失或格式无效。"""

    error_code: str = "TEAM_ANALYSIS_INVALID_INPUT"
    retryable: bool = False


class TeamAnalysisDataGapError(DataLayerError):
    """队伍分析数据缺口 — 部分精灵资料缺失，但输出了可计算部分。"""

    error_code: str = "TEAM_ANALYSIS_PARTIAL_DATA_GAP"
    retryable: bool = False

    def __init__(self, message: str, *, missing_sections: list[str] | None = None):
        super().__init__(message)
        self.missing_sections = missing_sections or []
