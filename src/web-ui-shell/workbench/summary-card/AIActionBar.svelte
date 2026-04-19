<!--
  AI Action Bar Component
  
  Handles AI review request with draft preservation.
  Corresponds to PRD US-004 [REQ-004]
-->

<script lang="ts">
  import type { TeamDraft } from "../host/types";
  import type { TeamAnalysisSnapshot } from "../draft-store/types";
  import type { AIActionState } from "./types";
  import { requestAIReview } from "./aiActionBar";

  export let draft: TeamDraft | null = null;
  export let analysisSnapshot: TeamAnalysisSnapshot | null = null;

  let aiAction: AIActionState = {
    is_submitting: false,
    last_error: null,
    last_success: false,
  };
  let reviewContent: string | null = null;

  async function handleAIReview() {
    if (!draft) return;

    aiAction = {
      ...aiAction,
      is_submitting: true,
      last_error: null,
    };

    const { state, reviewContent: content } = await requestAIReview(
      draft,
      analysisSnapshot
    );

    aiAction = state;
    reviewContent = content;
  }
</script>

<div class="ai-action-bar">
  <div class="ai-action-header">
    <h3>AI 分析评价与建议</h3>
    <button 
      class="ai-review-button"
      on:click={handleAIReview}
      disabled={aiAction.is_submitting || !draft || draft.slots.length === 0}
    >
      {aiAction.is_submitting ? "分析中..." : "发起 AI 分析"}
    </button>
  </div>

  {#if aiAction.last_error}
    <div class="ai-action-error">
      <p class="error-message">{aiAction.last_error}</p>
      <p class="error-hint">草稿已保存，您可以稍后重试</p>
    </div>
  {/if}

  {#if reviewContent}
    <div class="ai-review-result">
      <h4>分析结果</h4>
      <pre class="review-content">{reviewContent}</pre>
    </div>
  {/if}

  {#if !draft || draft.slots.length === 0}
    <p class="ai-action-hint">请先添加精灵到队伍后再发起 AI 分析</p>
  {/if}
</div>

<style>
  .ai-action-bar {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f9fafb;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .ai-action-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .ai-action-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #1f2937;
  }

  .ai-review-button {
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    border: 1px solid #3b82f6;
    background-color: #3b82f6;
    color: white;
    font-weight: 500;
    cursor: pointer;
    font-size: 0.875rem;
  }

  .ai-review-button:hover:not(:disabled) {
    background-color: #2563eb;
  }

  .ai-review-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .ai-action-error {
    background-color: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 0.375rem;
    padding: 0.75rem;
  }

  .error-message {
    color: #991b1b;
    font-weight: 600;
    margin: 0 0 0.25rem 0;
    font-size: 0.875rem;
  }

  .error-hint {
    color: #7f1d1d;
    margin: 0;
    font-size: 0.75rem;
  }

  .ai-review-result {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 0.75rem;
  }

  .ai-review-result h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: #1f2937;
  }

  .review-content {
    margin: 0;
    white-space: pre-wrap;
    font-family: inherit;
    font-size: 0.875rem;
    color: #374151;
    line-height: 1.5;
  }

  .ai-action-hint {
    color: #6b7280;
    font-size: 0.875rem;
    margin: 0;
    font-style: italic;
  }
</style>
