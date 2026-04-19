/**
 * Summary Card Module
 * 
 * Exports for summary payload rendering, AI action bar, and Wiki deep-read interaction.
 * Corresponds to web-ui-system.md §4.2 - Summary Card Host
 */

export type {
  SummaryRenderMode,
  SummaryPayload,
  SummaryCardRenderResult,
  WikiLinkInfo,
  AIActionState,
  SummaryCardHostState,
} from "./types";

export {
  renderSummaryCards,
  extractWikiLink,
  DEFAULT_RENDER_POLICY,
  type RenderPolicy,
} from "./summaryCardHost";

export {
  requestAIReview,
  type IWorkbenchGateway,
  type AIReviewRequest,
  type AIReviewResponse,
} from "./aiActionBar";

// Note: SummaryCardView.svelte and AIActionBar.svelte are used directly in Open WebUI context
