/**
 * Analysis Refresh Implementation
 * 
 * Implements refresh_team_analysis operation from web-ui-system.detail.md §3.13
 * Handles async analysis refresh with stale protection using request IDs.
 */

import type { TeamDraft } from "../host/types";
import type {
  AnalysisRefreshRequest,
  AnalysisRefreshResponse,
  TeamAnalysisSnapshot,
  LocalStateGuard,
} from "./types";

/**
 * Gateway interface for team analysis requests
 */
export interface IWorkbenchGateway {
  newRequestId(): string;
  requestTeamAnalysis(payload: AnalysisRefreshRequest): Promise<AnalysisRefreshResponse>;
}

/**
 * Mock gateway for testing (replace with actual HTTP client in production)
 */
class MockWorkbenchGateway implements IWorkbenchGateway {
  private requestIdCounter = 0;

  newRequestId(): string {
    return `req_${Date.now()}_${this.requestIdCounter++}`;
  }

  async requestTeamAnalysis(payload: AnalysisRefreshRequest): Promise<AnalysisRefreshResponse> {
    // Simulate async delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Mock response - in production this would call the actual backend
    return {
      request_id: payload.request_id,
      status: "success",
      snapshot: {
        schema_version: "v1",
        offensive_distribution: {
          物理攻击: 40,
          魔法攻击: 35,
          速度: 25,
        },
        attack_coverage: ["草系", "水系", "火系"],
        defensive_focus: ["物理防御", "魔法防御"],
        high_resistance: ["草系", "水系"],
        weak_against: ["火系", "飞行系"],
        metadata: {
          analysis_timestamp: new Date().toISOString(),
          draft_fingerprint: JSON.stringify(payload.team_draft.slots),
        },
      },
    };
  }
}

/**
 * Refresh team analysis with stale protection
 * 
 * Corresponds to web-ui-system.detail.md §3.13
 * 
 * @param draft - Current team draft
 * @param guard - Local state guard
 * @param gateway - Workbench gateway for analysis requests
 * @returns Updated guard and analysis result
 */
export async function refreshTeamAnalysis(
  draft: TeamDraft,
  guard: LocalStateGuard,
  gateway: IWorkbenchGateway = new MockWorkbenchGateway()
): Promise<{ guard: LocalStateGuard; result: AnalysisRefreshResponse }> {
  // Check if already analyzing
  if (guard.is_analyzing) {
    console.warn("Analysis refresh blocked: already analyzing");
    return {
      guard,
      result: {
        request_id: guard.last_analysis_request_id || "",
        status: "error",
        error: "Analysis already in progress",
      },
    };
  }

  // Generate new request ID
  const requestId = gateway.newRequestId();

  // Update draft with new request ID
  const updatedDraft: TeamDraft = {
    ...draft,
    last_analysis_request_id: requestId,
  };

  // Update guard to analyzing state
  const analyzingGuard: LocalStateGuard = {
    ...guard,
    is_analyzing: true,
    last_analysis_request_id: requestId,
  };

  // Save updated draft (in production, this would use the draft store)
  // For now, we'll just update the in-memory draft reference
  // The caller is responsible for persisting the updated draft

  try {
    // Request analysis from gateway
    const response = await gateway.requestTeamAnalysis({
      request_id: requestId,
      team_draft: updatedDraft,
    });

    // Check for stale response
    if (response.request_id !== analyzingGuard.last_analysis_request_id) {
      console.warn("Stale analysis response ignored");
      return {
        guard: analyzingGuard,
        result: {
          request_id: response.request_id,
          status: "stale_ignored",
        },
      };
    }

    // Release guard
    const releasedGuard: LocalStateGuard = {
      ...analyzingGuard,
      is_analyzing: false,
    };

    return { guard: releasedGuard, result: response };
  } catch (error) {
    console.error("Analysis refresh failed:", error);

    // Release guard on error
    const errorGuard: LocalStateGuard = {
      ...analyzingGuard,
      is_analyzing: false,
    };

    return {
      guard: errorGuard,
      result: {
        request_id: requestId,
        status: "error",
        error: error instanceof Error ? error.message : "Unknown error",
      },
    };
  }
}

/**
 * Check if analysis snapshot is stale relative to current draft
 */
export function isAnalysisStale(
  snapshot: TeamAnalysisSnapshot | null,
  draft: TeamDraft
): boolean {
  if (!snapshot) return true;
  if (!snapshot.metadata) return true;
  if (!draft.last_analysis_request_id) return true;

  // Compare draft fingerprint with snapshot metadata
  const currentFingerprint = JSON.stringify(draft.slots);
  return snapshot.metadata.draft_fingerprint !== currentFingerprint;
}
