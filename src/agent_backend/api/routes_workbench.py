"""
工作台 API Routes — Team Analysis 与 AI Review 端点。

对齐: agent-backend-system.md §5.3 HTTP API 端点摘要
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import ValidationError

from ..app.session_service import SessionIdentityError, resolve_session_key
from ..integrations.data_layer_client import IDataLayerClient
from .error_mapping import (
    ProductError,
    from_session_identity_error,
    from_validation_exception,
    team_ai_review_error,
    team_analysis_error,
    validation_error,
)
from .schemas_workbench import (
    AIReviewRequest,
    AIReviewResponse,
    TeamAnalysisRequest,
    TeamAnalysisResponse,
)

router = APIRouter(prefix="/v1/workbench", tags=["workbench"])


def get_data_layer_client(request: Request) -> IDataLayerClient:
    """获取 data-layer client 实例（从 app state）。"""
    return request.app.state.data_layer_client


@router.post("/team-analysis", response_model=TeamAnalysisResponse)
async def request_team_analysis(request: Request, payload: TeamAnalysisRequest) -> Response:
    """队伍分析端点 — 消费 TeamDraft 并返回结构化 TeamAnalysisSnapshot。

    对齐: agent-backend-system.detail.md §3.11
    """
    try:
        # 解析 session key
        headers = dict(request.headers)
        session_key = resolve_session_key(headers)

        # 调用 data-layer 分析
        data_layer = get_data_layer_client(request)
        team_draft_dict = payload.team_draft.model_dump()

        result = await data_layer.analyze_team_draft(team_draft_dict)

        if not result["success"]:
            return team_analysis_error(
                reason=result.get("error_message", "未知错误"),
            ).to_response()

        # 构建响应
        response = TeamAnalysisResponse(
            schema_version="v1",
            team_snapshot=result["team_snapshot"],
            wiki_targets=[],  # TODO: 从 snapshot 提取 wiki_targets
        )

        return Response(content=response.model_dump_json(), media_type="application/json")

    except SessionIdentityError as exc:
        return from_session_identity_error(exc).to_response()
    except ValidationError as exc:
        return from_validation_exception(exc).to_response()
    except ProductError as exc:
        return exc.to_response()
    except Exception as exc:
        return team_analysis_error(reason=str(exc)).to_response()


@router.post("/ai-review", response_model=AIReviewResponse)
async def review_team_draft(request: Request, payload: AIReviewRequest) -> Response:
    """AI 评价端点 — 消费 TeamDraft + TeamAnalysisSnapshot 并返回结构化 AI 建议。

    对齐: agent-backend-system.detail.md §3.12

    注意: T3.2.1 阶段使用 snapshot 生成结构化建议，不调用 LLM。
    """
    try:
        # 解析 session key
        headers = dict(request.headers)
        session_key = resolve_session_key(headers)

        # 使用 snapshot 生成结构化建议（不调用 LLM，基于 snapshot 分析）
        snapshot = payload.team_snapshot
        team_draft = payload.team_draft

        # 基于 snapshot 生成建议
        review_summary = _generate_review_from_snapshot(snapshot)
        suggestions = _generate_suggestions_from_snapshot(snapshot)

        response = AIReviewResponse(
            schema_version="v1",
            review_summary=review_summary,
            suggestions=suggestions,
            metadata={
                "session_key": session_key,
                "snapshot_schema_version": snapshot.get("schema_version"),
                "slots_count": len(team_draft.slots),
                "uses_snapshot": True,
            },
        )

        return Response(content=response.model_dump_json(), media_type="application/json")

    except SessionIdentityError as exc:
        return from_session_identity_error(exc).to_response()
    except ValidationError as exc:
        return from_validation_exception(exc).to_response()
    except ProductError as exc:
        return exc.to_response()
    except Exception as exc:
        return team_ai_review_error(reason=str(exc)).to_response()


def _generate_review_from_snapshot(snapshot: dict) -> str:
    """基于 snapshot 生成评价摘要（不调用 LLM）。"""
    if not snapshot:
        return "队伍分析快照为空，无法生成评价。"

    schema_version = snapshot.get("schema_version")
    if schema_version != "v1":
        return f"队伍分析快照版本不匹配: {schema_version}"

    # 检查 snapshot 中的关键部分
    attack_distribution = snapshot.get("attack_distribution", {})
    defense_focus = snapshot.get("defense_focus", {})
    missing_data_notes = snapshot.get("missing_data_notes", [])

    if missing_data_notes:
        return f"队伍分析存在数据缺失: {', '.join(missing_data_notes)}"

    status = attack_distribution.get("status", "unknown")
    if status == "insufficient_data":
        return "队伍数据不足，建议补充精灵资料后重新分析。"

    # 基于可用数据生成评价
    review_parts = []
    if status == "balanced":
        review_parts.append("队伍攻击分布均衡")
    elif status == "focused":
        review_parts.append("队伍攻击集中")
    else:
        review_parts.append("队伍攻击分布需优化")

    return "，".join(review_parts) + "。"


def _generate_suggestions_from_snapshot(snapshot: dict) -> list[str]:
    """基于 snapshot 生成建议列表（不调用 LLM）。"""
    suggestions = []

    attack_distribution = snapshot.get("attack_distribution", {})
    defense_focus = snapshot.get("defense_focus", {})

    # 基于攻击分布生成建议
    status = attack_distribution.get("status")
    if status == "insufficient_data":
        suggestions.append("建议补充精灵资料以获取更准确的分析")
    elif status == "focused":
        suggestions.append("建议增加属性多样性以提高队伍适应性")

    # 基于防御重点生成建议
    if defense_focus:
        suggestions.append("建议根据防御重点调整队伍配置")

    if not suggestions:
        suggestions.append("队伍结构良好，可根据实际战斗需求微调")

    return suggestions
