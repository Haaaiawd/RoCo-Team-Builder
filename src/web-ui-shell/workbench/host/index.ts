/**
 * Workbench Host Module
 * 
 * Exports for Team Workbench Host with dual entry points and handoff fallback.
 * Corresponds to web-ui-system.md §4.2 - Team Workbench Host
 * 
 * Note: The WorkbenchHost.svelte component is used directly in Open WebUI context,
 * not exported through this TypeScript index.
 */

export type { 
  WorkbenchEntryPoint,
  TeamDraftSource,
  TeamDraft,
  TeamDraftSlot,
  WorkbenchHandOffPayload,
  TeamWorkbenchUiState,
} from "./types";

export { 
  hydrateWorkbenchFromEntry,
  saveDraft,
  clearDraft,
} from "./hydration";
