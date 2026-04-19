/**
 * Workbench Host Types
 * 
 * Shared types for Team Workbench Host and handoff hydration.
 * Aligned with web-ui-system.detail.md §2
 */

export type WorkbenchEntryPoint = "sidebar" | "agent_handoff";

export type TeamDraftSource = "empty" | "agent_handoff" | "imported" | "manual";

export interface TeamDraftSlot {
  slot_index: number;
  spirit_id: string | null;
  spirit_name: string | null;
  skill_ids: string[];
  skill_names: string[];
  wiki_slug: string | null;
}

export interface TeamDraft {
  schema_version: string;
  source: TeamDraftSource;
  entry_point: WorkbenchEntryPoint;
  slots: TeamDraftSlot[];
  analysis_view: Record<string, string | string[] | null>;
  summary_targets: number[];
  last_analysis_request_id: string | null;
}

export interface WorkbenchHandOffPayload {
  schema_version: string;
  team_draft: TeamDraft;
  metadata?: {
    session_key?: string;
    snapshot_schema_version?: string;
  };
}

export interface TeamWorkbenchUiState {
  handoff_status: "idle" | "hydrating" | "failed" | "ready";
  analysis_status: "idle" | "refreshing" | "ready" | "partial_error";
  ai_review_status: "idle" | "submitting" | "ready" | "failed";
  import_status: "idle" | "parsing" | "ready" | "failed";
  export_status: "idle" | "exporting" | "ready" | "failed";
  dirty: boolean;
  last_error_code: string | null;
}
