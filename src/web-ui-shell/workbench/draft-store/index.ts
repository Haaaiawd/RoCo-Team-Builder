/**
 * Draft Store Module
 * 
 * Exports for TeamDraft store, analysis refresh, and local state guards.
 * Corresponds to web-ui-system.md §4.2 - Team Draft Store
 */

export type {
  DraftMutationType,
  DraftMutation,
  AnalysisRefreshRequest,
  AnalysisRefreshResponse,
  TeamAnalysisSnapshot,
  LocalStateGuard,
  DraftStoreState,
} from "./types";

export {
  mutateTeamDraft,
  loadDraft,
  loadGuard,
  initializeDraftStore,
} from "./draftStore";

export {
  refreshTeamAnalysis,
  isAnalysisStale,
  IWorkbenchGateway,
} from "./analysisRefresh";

// Note: AnalysisView.svelte is used directly in Open WebUI context
