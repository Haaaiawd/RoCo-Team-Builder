/**
 * Draft Store Implementation
 * 
 * Implements mutate_team_draft operation from web-ui-system.detail.md §3.12
 * Handles draft mutations with shared field separation and local state guards.
 */

import type { TeamDraft, TeamDraftSlot } from "../host/types";
import type { DraftMutation, LocalStateGuard, DraftStoreState } from "./types";

const DRAFT_STORAGE_KEY = "team_draft:v1";
const GUARD_STORAGE_KEY = "team_draft_guard:v1";

/**
 * Local storage interface for draft and guard persistence
 */
interface DraftStorage {
  load(key: string): TeamDraft | LocalStateGuard | null;
  save(key: string, data: TeamDraft | LocalStateGuard): void;
}

class LocalStorageDraftStorage implements DraftStorage {
  load(key: string): TeamDraft | LocalStateGuard | null {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;
      return JSON.parse(item);
    } catch (error) {
      console.error("Failed to load from storage:", error);
      return null;
    }
  }

  save(key: string, data: TeamDraft | LocalStateGuard): void {
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.error("Failed to save to storage:", error);
    }
  }
}

const storage = new LocalStorageDraftStorage();

/**
 * Initialize local state guard
 */
function createGuard(): LocalStateGuard {
  return {
    is_mutating: false,
    is_analyzing: false,
    last_mutation_timestamp: Date.now(),
    last_analysis_request_id: null,
    pending_mutation_count: 0,
  };
}

/**
 * Apply mutation to team draft slot
 * 
 * Corresponds to web-ui-system.detail.md §3.12
 */
function applySlotMutation(slot: TeamDraftSlot, mutation: DraftMutation): TeamDraftSlot {
  const updated = { ...slot };
  
  if (mutation.spirit_id !== undefined) updated.spirit_id = mutation.spirit_id;
  if (mutation.spirit_name !== undefined) updated.spirit_name = mutation.spirit_name;
  if (mutation.skill_ids !== undefined) updated.skill_ids = mutation.skill_ids;
  if (mutation.skill_names !== undefined) updated.skill_names = mutation.skill_names;
  if (mutation.wiki_slug !== undefined) updated.wiki_slug = mutation.wiki_slug;
  
  return updated;
}

/**
 * Mutate team draft with guard protection
 * 
 * Corresponds to web-ui-system.detail.md §3.12
 * 
 * @param draft - Current team draft
 * @param mutation - Mutation to apply
 * @param guard - Local state guard
 * @returns Updated draft and guard
 */
export function mutateTeamDraft(
  draft: TeamDraft,
  mutation: DraftMutation,
  guard?: LocalStateGuard
): { draft: TeamDraft; guard: LocalStateGuard } {
  // Initialize guard if not provided
  const activeGuard = guard || createGuard();
  
  // Check if guard allows mutation
  if (activeGuard.is_mutating) {
    console.warn("Mutation blocked: draft is already being mutated");
    return { draft, guard: activeGuard };
  }
  
  // Set guard to mutating state
  const mutatingGuard: LocalStateGuard = {
    ...activeGuard,
    is_mutating: true,
    last_mutation_timestamp: Date.now(),
    pending_mutation_count: activeGuard.pending_mutation_count + 1,
  };
  
  // Apply mutation
  const updatedDraft = { ...draft };
  
  if (mutation.slot_index !== undefined && mutation.slot_index !== null) {
    // Slot mutation
    const slotIndex = mutation.slot_index;
    
    // Ensure slots array has enough elements
    while (updatedDraft.slots.length <= slotIndex) {
      updatedDraft.slots.push({
        slot_index: updatedDraft.slots.length,
        spirit_id: null,
        spirit_name: null,
        skill_ids: [],
        skill_names: [],
        wiki_slug: null,
      });
    }
    
    // Apply mutation to slot
    if (mutation.type === "clear_slot") {
      updatedDraft.slots[slotIndex] = {
        slot_index: slotIndex,
        spirit_id: null,
        spirit_name: null,
        skill_ids: [],
        skill_names: [],
        wiki_slug: null,
      };
    } else {
      updatedDraft.slots[slotIndex] = applySlotMutation(
        updatedDraft.slots[slotIndex],
        mutation
      );
    }
  }
  
  // Analysis view mutation
  if (mutation.analysis_view !== undefined) {
    updatedDraft.analysis_view = {
      ...updatedDraft.analysis_view,
      ...mutation.analysis_view,
    };
  }
  
  // Summary targets mutation
  if (mutation.summary_targets !== undefined) {
    updatedDraft.summary_targets = mutation.summary_targets;
  }
  
  // Save to storage
  storage.save(DRAFT_STORAGE_KEY, updatedDraft);
  
  // Release guard
  const releasedGuard: LocalStateGuard = {
    ...mutatingGuard,
    is_mutating: false,
    pending_mutation_count: mutatingGuard.pending_mutation_count - 1,
  };
  
  storage.save(GUARD_STORAGE_KEY, releasedGuard);
  
  return { draft: updatedDraft, guard: releasedGuard };
}

/**
 * Load draft from storage
 */
export function loadDraft(): TeamDraft | null {
  return storage.load(DRAFT_STORAGE_KEY) as TeamDraft | null;
}

/**
 * Load guard from storage
 */
export function loadGuard(): LocalStateGuard | null {
  return storage.load(GUARD_STORAGE_KEY) as LocalStateGuard | null;
}

/**
 * Initialize draft store state
 */
export function initializeDraftStore(): DraftStoreState {
  const draft = loadDraft();
  const guard = loadGuard() || createGuard();
  
  return {
    draft: draft || {
      schema_version: "v1",
      source: "empty",
      entry_point: "sidebar",
      slots: [],
      analysis_view: {},
      summary_targets: [],
      last_analysis_request_id: null,
    },
    guard,
    analysis_snapshot: null,
    analysis_error: null,
  };
}
