/**
 * Workbench Hydration Logic
 * 
 * Implements hydrate_workbench_from_entry operation from web-ui-system.detail.md §3.11
 * Handles dual entry points (sidebar / agent_handoff) and handoff failure fallback.
 */

import type { TeamDraft, WorkbenchEntryPoint, WorkbenchHandOffPayload } from "./types";

const DRAFT_STORAGE_KEY = "team_draft:v1";
const SCHEMA_VERSION = "v1";

/**
 * Local storage interface for draft persistence
 */
interface DraftStorage {
  load(key: string): TeamDraft | null;
  save(key: string, draft: TeamDraft): void;
}

class LocalStorageDraftStorage implements DraftStorage {
  load(key: string): TeamDraft | null {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;
      return JSON.parse(item);
    } catch (error) {
      console.error("Failed to load draft from storage:", error);
      return null;
    }
  }

  save(key: string, draft: TeamDraft): void {
    try {
      localStorage.setItem(key, JSON.stringify(draft));
    } catch (error) {
      console.error("Failed to save draft to storage:", error);
    }
  }
}

const storage = new LocalStorageDraftStorage();

/**
 * Create an empty team draft
 */
function createEmptyDraft(entryPoint: WorkbenchEntryPoint): TeamDraft {
  return {
    schema_version: SCHEMA_VERSION,
    source: "empty",
    entry_point: entryPoint,
    slots: [],
    analysis_view: {},
    summary_targets: [],
    last_analysis_request_id: null,
  };
}

/**
 * Validate handoff payload structure
 */
function isValidHandoffPayload(payload: unknown): payload is WorkbenchHandOffPayload {
  if (!payload || typeof payload !== "object") return false;
  const p = payload as WorkbenchHandOffPayload;
  return (
    typeof p.schema_version === "string" &&
    typeof p.team_draft === "object" &&
    p.team_draft !== null
  );
}

/**
 * Hydrate workbench from entry point
 * 
 * Corresponds to web-ui-system.detail.md §3.11
 * 
 * @param entryPoint - Entry point: "sidebar" or "agent_handoff"
 * @param handoffPayload - Optional handoff payload from agent result
 * @returns TeamDraft to load into workbench
 */
export function hydrateWorkbenchFromEntry(
  entryPoint: WorkbenchEntryPoint,
  handoffPayload: unknown | null
): { draft: TeamDraft; error: string | null } {
  try {
    if (entryPoint === "sidebar") {
      // Try to load cached draft first
      const cached = storage.load(DRAFT_STORAGE_KEY);
      if (cached && cached.schema_version === SCHEMA_VERSION) {
        return { draft: cached, error: null };
      }
      // Fall back to empty draft
      return { draft: createEmptyDraft("sidebar"), error: null };
    }

    if (entryPoint === "agent_handoff") {
      // Validate and use handoff payload
      if (handoffPayload && isValidHandoffPayload(handoffPayload)) {
        const draft = handoffPayload.team_draft;
        if (draft.schema_version === SCHEMA_VERSION) {
          return { draft, error: null };
        }
        return {
          draft: createEmptyDraft("agent_handoff"),
          error: "HANDOFF_SCHEMA_VERSION_MISMATCH",
        };
      }
      // Handoff payload invalid or missing - fall back to empty draft
      return {
        draft: createEmptyDraft("agent_handoff"),
        error: "HANDOFF_PAYLOAD_INVALID",
      };
    }

    return {
      draft: createEmptyDraft("sidebar" as WorkbenchEntryPoint),
      error: "UNKNOWN_ENTRY_POINT",
    };
  } catch (error) {
    console.error("Hydration error:", error);
    return {
      draft: createEmptyDraft(entryPoint),
      error: "HANDOFF_HYDRATION_ERROR",
    };
  }
}

/**
 * Save current draft to local storage
 */
export function saveDraft(draft: TeamDraft): void {
  storage.save(DRAFT_STORAGE_KEY, draft);
}

/**
 * Clear draft from local storage
 */
export function clearDraft(): void {
  localStorage.removeItem(DRAFT_STORAGE_KEY);
}
