<!--
  Summary Card View Component
  
  Renders summary payload with fallback text support.
  Corresponds to web-ui-system.detail.md §3.17
-->

<script lang="ts">
  import type { SummaryPayload, SummaryCardRenderResult, WikiLinkInfo } from "./types";
  import { renderSummaryCards, extractWikiLink, DEFAULT_RENDER_POLICY } from "./summaryCardHost";

  export let summaryPayload: SummaryPayload | null = null;
  export let spiritName: string = "";

  let renderResult: SummaryCardRenderResult | null = null;
  let wikiLink: WikiLinkInfo | null = null;

  $: if (summaryPayload) {
    renderResult = renderSummaryCards(summaryPayload, DEFAULT_RENDER_POLICY);
    wikiLink = extractWikiLink(summaryPayload);
  }
</script>

<div class="summary-card-view">
  {#if !summaryPayload}
    <p class="no-summary">暂无摘要信息</p>
  {:else if renderResult?.mode === "summary_card"}
    <div class="summary-card">
      <div class="summary-header">
        <h3>{spiritName} - 精灵摘要</h3>
        {#if wikiLink?.is_available}
          <a 
            href={wikiLink.wiki_url || "#"} 
            target="_blank" 
            rel="noopener noreferrer"
            class="wiki-link"
          >
            Wiki 深读 →
          </a>
        {:else if wikiLink}
          <span class="wiki-link unavailable">
            Wiki 暂不可用
          </span>
        {/if}
      </div>
      <div class="summary-content">
        {@html renderResult.html || ""}
      </div>
    </div>
  {:else if renderResult?.mode === "fallback_text"}
    <div class="summary-fallback">
      <div class="fallback-header">
        <h3>{spiritName} - 精灵摘要</h3>
        {#if wikiLink?.is_available}
          <a 
            href={wikiLink.wiki_url || "#"} 
            target="_blank" 
            rel="noopener noreferrer"
            class="wiki-link"
          >
            Wiki 深读 →
          </a>
        {:else if wikiLink}
          <span class="wiki-link unavailable">
            Wiki 暂不可用
          </span>
        {/if}
      </div>
      <p class="fallback-text">{renderResult.content}</p>
    </div>
  {/if}
</div>

<style>
  .summary-card-view {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f9fafb;
  }

  .no-summary {
    color: #9ca3af;
    font-style: italic;
    margin: 0;
  }

  .summary-card,
  .summary-fallback {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .summary-header,
  .fallback-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 0.5rem;
  }

  .summary-header h3,
  .fallback-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #1f2937;
  }

  .wiki-link {
    color: #3b82f6;
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .wiki-link:hover {
    text-decoration: underline;
  }

  .wiki-link.unavailable {
    color: #9ca3af;
    cursor: not-allowed;
  }

  .summary-content {
    color: #374151;
    line-height: 1.5;
  }

  .fallback-text {
    color: #4b5563;
    margin: 0;
    line-height: 1.5;
  }
</style>
