/**
 * AI Action Bar Implementation
 * 
 * Handles AI review request from workbench with draft preservation.
 * Corresponds to PRD US-004 [REQ-004]
 */

import type { TeamDraft } from "../host/types";
import type { TeamAnalysisSnapshot } from "../draft-store/types";
import type { AIActionState } from "./types";

/**
 * Gateway interface for AI review requests
 */
export interface IWorkbenchGateway {
  requestAIReview(payload: AIReviewRequest): Promise<AIReviewResponse>;
}

/**
 * AI review request payload
 */
export interface AIReviewRequest {
  team_draft: TeamDraft;
  analysis_snapshot: TeamAnalysisSnapshot | null;
  request_id: string;
}

/**
 * AI review response
 */
export interface AIReviewResponse {
  request_id: string;
  status: "success" | "failed";
  review_content?: string;
  error?: string;
}

/**
 * Mock gateway for testing (replace with actual HTTP client in production)
 */
class MockWorkbenchGateway implements IWorkbenchGateway {
  async requestAIReview(payload: AIReviewRequest): Promise<AIReviewResponse> {
    // Simulate async delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Mock response - in production this would call the actual backend
    return {
      request_id: payload.request_id,
      status: "success",
      review_content: "基于当前队伍配置分析：\n\n" +
        "1. 攻击覆盖：队伍具备草系和水系攻击覆盖，建议补充火系以形成完整三角克制。\n" +
        "2. 防守侧重点：当前队伍物理防御较强，建议增加一只高魔法防御的精灵。\n" +
        "3. 技能搭配：建议为第一槽位精灵增加控制技能，提升队伍容错率。\n\n" +
        "总体评价：队伍结构较为均衡，适合中等难度副本。建议按上述建议调整后挑战高难度内容。",
    };
  }
}

/**
 * Request AI review with draft preservation
 * 
 * @param draft - Current team draft
 * @param analysis_snapshot - Current analysis snapshot
 * @param gateway - Workbench gateway
 * @returns Updated AI action state and review content
 */
export async function requestAIReview(
  draft: TeamDraft,
  analysis_snapshot: TeamAnalysisSnapshot | null,
  gateway: IWorkbenchGateway = new MockWorkbenchGateway()
): Promise<{ state: AIActionState; reviewContent: string | null }> {
  const request_id = `ai_review_${Date.now()}`;

  // Check if draft has at least one spirit
  if (!draft || draft.slots.length === 0 || !draft.slots.some((s) => s.spirit_id)) {
    return {
      state: {
        is_submitting: false,
        last_error: "请先完成基础配队后再发起 AI 分析",
        last_success: false,
      },
      reviewContent: null,
    };
  }

  try {
    const response = await gateway.requestAIReview({
      team_draft: draft,
      analysis_snapshot: analysis_snapshot,
      request_id,
    });

    if (response.status === "success" && response.review_content) {
      return {
        state: {
          is_submitting: false,
          last_error: null,
          last_success: true,
        },
        reviewContent: response.review_content,
      };
    } else {
      return {
        state: {
          is_submitting: false,
          last_error: response.error || "AI 分析请求失败",
          last_success: false,
        },
        reviewContent: null,
      };
    }
  } catch (error) {
    console.error("AI review request failed:", error);

    return {
      state: {
        is_submitting: false,
        last_error: error instanceof Error ? error.message : "AI 分析请求失败",
        last_success: false,
      },
      reviewContent: null,
    };
  }
}
