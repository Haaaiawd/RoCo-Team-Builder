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

    注意: 当前为骨架实现，返回模拟响应。T3.2.1 将接入实际 LLM 调用。
    """
    try:
        # 解析 session key
        headers = dict(request.headers)
        session_key = resolve_session_key(headers)

        # 骨架实现：返回模拟 AI 建议
        # TODO: T3.2.1 接入实际 LLM 调用
        response = AIReviewResponse(
            schema_version="v1",
            review_summary="队伍结构良好，建议补充属性多样性。",
            suggestions=[
                "建议增加火属性精灵以增强攻击",
                "水属性精灵可作为防御补充",
            ],
            metadata={
                "session_key": session_key,
                "snapshot_schema_version": payload.team_snapshot.get("schema_version"),
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
