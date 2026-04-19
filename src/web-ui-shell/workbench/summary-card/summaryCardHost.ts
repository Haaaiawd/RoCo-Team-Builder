/**
 * Summary Card Host Implementation
 * 
 * Implements render_summary_cards operation from web-ui-system.detail.md §3.17
 * Handles summary payload rendering with fallback text support.
 */

import type { SummaryPayload, SummaryCardRenderResult, WikiLinkInfo } from "./types";

/**
 * Render policy for summary cards
 */
export interface RenderPolicy {
  rich_ui_enabled: boolean;
}

/**
 * Render summary cards with fallback support
 * 
 * Corresponds to web-ui-system.detail.md §3.17
 * 
 * @param summary_payload - Summary payload from spirit-card-system
 * @param policy - Render policy
 * @returns Render result with mode and content
 */
export function renderSummaryCards(
  summary_payload: SummaryPayload,
  policy: RenderPolicy
): SummaryCardRenderResult {
  if (!policy.rich_ui_enabled) {
    return {
      mode: "fallback_text",
      content: summary_payload.fallback_text || "摘要信息暂不可用",
    };
  }

  if (summary_payload.html) {
    return {
      mode: "summary_card",
      html: summary_payload.html,
    };
  }

  return {
    mode: "fallback_text",
    content: summary_payload.fallback_text || "摘要信息暂不可用",
  };
}

/**
 * Extract Wiki link information from summary payload
 * 
 * @param summary_payload - Summary payload
 * @returns Wiki link information
 */
export function extractWikiLink(summary_payload: SummaryPayload): WikiLinkInfo {
  const wiki_slug = summary_payload.metadata?.wiki_slug || null;
  
  if (!wiki_slug) {
    return {
      wiki_slug: null,
      wiki_url: null,
      is_available: false,
    };
  }

  // In production, construct actual Wiki URL
  // For now, return placeholder URL
  const wiki_url = `https://wiki.biligame.com/roco/${wiki_slug}`;
  
  return {
    wiki_slug,
    wiki_url,
    is_available: true,
  };
}

/**
 * Default render policy (rich UI enabled)
 */
export const DEFAULT_RENDER_POLICY: RenderPolicy = {
  rich_ui_enabled: true,
};
