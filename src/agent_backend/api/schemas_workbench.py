"""
工作台 API Schemas — TeamAnalysis 与 AI Review 的请求/响应结构。

对齐: agent-backend-system.md §5.3 HTTP API 端点摘要
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeamDraftSlot(BaseModel):
    """队伍草稿槽位。"""

    model_config = ConfigDict(extra="forbid")

    slot_index: int
    spirit_name: str
    skills: list[str] = Field(default_factory=list)


class TeamDraftRequest(BaseModel):
    """队伍草稿请求。"""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = "v1"
    slots: list[TeamDraftSlot]

    @field_validator("slots")
    @classmethod
    def validate_slots(cls, value: list[TeamDraftSlot]) -> list[TeamDraftSlot]:
        if not value:
            raise ValueError("slots must not be empty")
        return value


class TeamAnalysisRequest(BaseModel):
    """队伍分析请求。"""

    model_config = ConfigDict(extra="forbid")

    team_draft: TeamDraftRequest
    user_note: str | None = None


class AIReviewRequest(BaseModel):
    """AI 评价请求。"""

    model_config = ConfigDict(extra="forbid")

    team_draft: TeamDraftRequest
    team_snapshot: dict  # TeamAnalysisSnapshot
    user_note: str | None = None

    @field_validator("team_snapshot")
    @classmethod
    def validate_snapshot(cls, value: dict) -> dict:
        if not value:
            raise ValueError("team_snapshot must not be empty")
        return value


class TeamAnalysisResponse(BaseModel):
    """队伍分析响应。"""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = "v1"
    team_snapshot: dict  # TeamAnalysisSnapshot
    wiki_targets: list[dict] = Field(default_factory=list)


class AIReviewResponse(BaseModel):
    """AI 评价响应。"""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = "v1"
    review_summary: str
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
