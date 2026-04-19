/**
 * Draft Store Types
 * 
 * Types for TeamDraft store, analysis refresh, and local state guards.
 * Aligned with web-ui-system.detail.md §2
 */

import type { TeamDraft, TeamDraftSlot } from "../host/types";

export type DraftMutationType = 
  | "set_spirit"
  | "set_skill"
  | "clear_slot"
  | "set_analysis_view"
  | "set_summary_targets";

export interface DraftMutation {
  type: DraftMutationType;
  slot_index?: number;
  spirit_id?: string | null;
  spirit_name?: string | null;
  skill_ids?: string[];
  skill_names?: string[];
  wiki_slug?: string | null;
  analysis_view?: Record<string, string | string[] | null>;
  summary_targets?: number[];
}

export interface AnalysisRefreshRequest {
  request_id: string;
  team_draft: TeamDraft;
}

export interface AnalysisRefreshResponse {
  request_id: string;
  status: "success" | "stale_ignored" | "error";
  snapshot?: TeamAnalysisSnapshot;
  error?: string;
}

export interface TeamAnalysisSnapshot {
  schema_version: string;
  offensive_distribution: Record<string, number>;
  attack_coverage: string[];
  defensive_focus: string[];
  high_resistance: string[];
  weak_against: string[];
  metadata?: {
    analysis_timestamp: string;
    draft_fingerprint: string;
  };
}

export interface LocalStateGuard {
  is_mutating: boolean;
  is_analyzing: boolean;
  last_mutation_timestamp: number;
  last_analysis_request_id: string | null;
  pending_mutation_count: number;
}

export interface DraftStoreState {
  draft: TeamDraft;
  guard: LocalStateGuard;
  analysis_snapshot: TeamAnalysisSnapshot | null;
  analysis_error: string | null;
}
