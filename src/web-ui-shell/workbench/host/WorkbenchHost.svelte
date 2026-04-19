<!--
  Team Workbench Host Component
  
  Implements dual entry workbench host with handoff fallback.
  Corresponds to web-ui-system.md §4.2 Core Components - Team Workbench Host
  
  Entry points:
  1. Sidebar entry - loads cached draft or creates empty draft
  2. Agent handoff entry - loads from handoff payload or falls back to empty draft
-->

<script lang="ts">
  import type { TeamDraft, WorkbenchHandOffPayload, TeamWorkbenchUiState } from "./types";
  import { hydrateWorkbenchFromEntry, saveDraft, clearDraft } from "./hydration";
  import { 
    mutateTeamDraft, 
    initializeDraftStore, 
    type DraftStoreState,
    type DraftMutation,
    refreshTeamAnalysis,
    type TeamAnalysisSnapshot
  } from "../draft-store";
  import AnalysisView from "../draft-store/AnalysisView.svelte";

  export let entryPoint: "sidebar" | "agent_handoff" = "sidebar";
  export let handoffPayload: WorkbenchHandOffPayload | null = null;

  let draft: TeamDraft | null = null;
  let storeState: DraftStoreState = initializeDraftStore();
  let uiState: TeamWorkbenchUiState = {
    handoff_status: "idle",
    analysis_status: "idle",
    ai_review_status: "idle",
    import_status: "idle",
    export_status: "idle",
    dirty: false,
    last_error_code: null,
  };
  let hydrationError: string | null = null;

  // Hydrate draft from entry point
  $: if (entryPoint || handoffPayload !== undefined) {
    uiState.handoff_status = "hydrating";
    
    const { draft: hydratedDraft, error } = hydrateWorkbenchFromEntry(entryPoint, handoffPayload);
    
    draft = hydratedDraft;
    hydrationError = error;
    
    if (error) {
      uiState.handoff_status = "failed";
      uiState.last_error_code = error;
    } else {
      uiState.handoff_status = "ready";
      // Initialize store state with hydrated draft
      storeState = initializeDraftStore();
      storeState.draft = hydratedDraft;
    }
  }

  async function handleRefreshAnalysis() {
    if (!draft) return;
    
    uiState.analysis_status = "refreshing";
    
    const { guard: updatedGuard, result } = await refreshTeamAnalysis(
      draft,
      storeState.guard
    );
    
    storeState.guard = updatedGuard;
    
    if (result.status === "success" && result.snapshot) {
      storeState.analysis_snapshot = result.snapshot;
      storeState.analysis_error = null;
      uiState.analysis_status = "ready";
      // Update draft with new request ID
      draft.last_analysis_request_id = result.request_id;
    } else if (result.status === "stale_ignored") {
      // Stale response - ignore, keep current state
      uiState.analysis_status = "ready";
    } else {
      storeState.analysis_error = result.error || "Analysis failed";
      uiState.analysis_status = "partial_error";
    }
  }

  function handleClearDraft() {
    clearDraft();
    draft = null;
    hydrationError = null;
    storeState = initializeDraftStore();
  }

  function handleSaveDraft() {
    if (draft) {
      saveDraft(draft);
      uiState.dirty = false;
    }
  }
</script>

<div class="workbench-host">
  <!-- Hydration Error Display -->
  {#if hydrationError}
    <div class="hydration-error-banner">
      <p class="error-message">
        {#if hydrationError === "HANDOFF_PAYLOAD_INVALID"}
          无法加载队伍草稿：承接载荷缺失或损坏
        {:else if hydrationError === "HANDOFF_SCHEMA_VERSION_MISMATCH"}
          无法加载队伍草稿：数据版本不匹配
        {:else}
          无法加载队伍草稿，已为您创建空白草稿
        {/if}
      </p>
      <p class="error-hint">您可以继续编辑空白草稿或从侧边栏重新进入工作台</p>
    </div>
  {/if}

  <!-- Workbench Content -->
  {#if draft}
    <div class="workbench-content">
      <header class="workbench-header">
        <h1>配队工作台</h1>
        <div class="draft-meta">
          <span class="draft-source">
            {draft.source === "agent_handoff" ? "来自 Agent 推荐" : "空白草稿"}
          </span>
          {#if uiState.dirty}
            <span class="dirty-indicator">未保存</span>
          {/if}
        </div>
      </header>

      <!-- Draft Slots -->
      <section class="draft-slots">
        <h2>队伍配置</h2>
        {#if draft.slots.length === 0}
          <p class="empty-draft-hint">暂无精灵配置，请添加精灵</p>
        {:else}
          <div class="slots-grid">
            {#each draft.slots as slot (slot.slot_index)}
              <div class="slot-card">
                <div class="slot-number">槽位 {slot.slot_index + 1}</div>
                {#if slot.spirit_name}
                  <div class="slot-content">
                    <div class="spirit-name">{slot.spirit_name}</div>
                    {#if slot.skill_names.length > 0}
                      <div class="skill-list">
                        {#each slot.skill_names as skill}
                          <span class="skill-tag">{skill}</span>
                        {/each}
                      </div>
                    {/if}
                  </div>
                {:else}
                  <div class="slot-empty">空槽位</div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </section>

      <!-- Analysis View -->
      <section class="analysis-section">
        <div class="analysis-header">
          <h2>队伍分析</h2>
          <button 
            class="refresh-button"
            on:click={handleRefreshAnalysis}
            disabled={uiState.analysis_status === "refreshing"}
          >
            {uiState.analysis_status === "refreshing" ? "分析中..." : "刷新分析"}
          </button>
        </div>
        <AnalysisView 
          snapshot={storeState.analysis_snapshot}
          isLoading={uiState.analysis_status === "refreshing"}
          error={storeState.analysis_error}
        />
      </section>

      <!-- Action Bar -->
      <footer class="workbench-actions">
        <button 
          class="action-button"
          on:click={handleSaveDraft}
          disabled={!uiState.dirty}
        >
          保存草稿
        </button>
        <button 
          class="action-button secondary"
          on:click={handleClearDraft}
        >
          清空草稿
        </button>
      </footer>
    </div>
  {/if}

  <!-- Loading State -->
  {#if uiState.handoff_status === "hydrating"}
    <div class="loading-state">
      <p>正在加载工作台...</p>
    </div>
  {/if}
</div>

<style>
  .workbench-host {
    padding: 1rem;
  }

  .hydration-error-banner {
    background-color: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .error-message {
    color: #991b1b;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .error-hint {
    color: #7f1d1d;
    margin: 0;
    font-size: 0.875rem;
  }

  .workbench-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .workbench-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 1rem;
  }

  .workbench-header h1 {
    margin: 0;
    font-size: 1.5rem;
    color: #1f2937;
  }

  .draft-meta {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .draft-source {
    color: #6b7280;
    font-size: 0.875rem;
  }

  .dirty-indicator {
    background-color: #fef3c7;
    color: #92400e;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .draft-slots h2 {
    margin: 0 0 1rem 0;
    font-size: 1.125rem;
    color: #1f2937;
  }

  .analysis-section {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f9fafb;
  }

  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .analysis-header h2 {
    margin: 0;
    font-size: 1.125rem;
    color: #1f2937;
  }

  .refresh-button {
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    border: 1px solid #d1d5db;
    background-color: white;
    color: #374151;
    font-weight: 500;
    cursor: pointer;
    font-size: 0.875rem;
  }

  .refresh-button:hover:not(:disabled) {
    background-color: #f3f4f6;
  }

  .refresh-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty-draft-hint {
    color: #6b7280;
    font-style: italic;
  }

  .slots-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .slot-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f9fafb;
  }

  .slot-number {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }

  .slot-empty {
    color: #9ca3af;
    font-style: italic;
  }

  .spirit-name {
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.5rem;
  }

  .skill-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .skill-tag {
    background-color: #dbeafe;
    color: #1e40af;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
  }

  .workbench-actions {
    display: flex;
    gap: 0.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .action-button {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    border: none;
    background-color: #3b82f6;
    color: white;
    font-weight: 500;
    cursor: pointer;
  }

  .action-button:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }

  .action-button.secondary {
    background-color: #e5e7eb;
    color: #1f2937;
  }

  .loading-state {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
  }
</style>
