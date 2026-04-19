/**
 * Summary Card Types
 * 
 * Types for summary payload rendering, AI action bar, and Wiki deep-read interaction.
 * Aligned with spirit-card-system.md §6.2 and web-ui-system.detail.md §3.17
 */

export type SummaryRenderMode = "summary_card" | "fallback_text";

export interface SummaryPayload {
  html?: string;
  fallback_text: string;
  metadata?: {
    spirit_id?: string;
    spirit_name?: string;
    wiki_slug?: string;
    render_mode?: SummaryRenderMode;
  };
}

export interface SummaryCardRenderResult {
  mode: SummaryRenderMode;
  html?: string;
  content?: string;
}

export interface WikiLinkInfo {
  wiki_slug: string | null;
  wiki_url: string | null;
  is_available: boolean;
}

export interface AIActionState {
  is_submitting: boolean;
  last_error: string | null;
  last_success: boolean;
}

export interface SummaryCardHostState {
  summary_payload: SummaryPayload | null;
  render_result: SummaryCardRenderResult | null;
  wiki_link: WikiLinkInfo;
  ai_action: AIActionState;
}
