<!--
  Analysis View Component
  
  Displays TeamAnalysisSnapshot with controlled empty state.
  Corresponds to web-ui-system.md §4.2 - Analysis View + Summary Card Host
-->

<script lang="ts">
  import type { TeamAnalysisSnapshot } from "./types";

  export let snapshot: TeamAnalysisSnapshot | null = null;
  export let isLoading: boolean = false;
  export let error: string | null = null;

  $: isEmpty = !snapshot && !isLoading && !error;
  $: hasData = snapshot !== null;
  $: hasError = error !== null;
</script>

<div class="analysis-view">
  <!-- Loading State -->
  {#if isLoading}
    <div class="analysis-loading">
      <p>正在分析队伍结构...</p>
    </div>
  {/if}

  <!-- Error State -->
  {#if hasError}
    <div class="analysis-error">
      <p class="error-message">分析失败：{error}</p>
      <p class="error-hint">请稍后重试或检查队伍配置</p>
    </div>
  {/if}

  <!-- Empty State -->
  {#if isEmpty}
    <div class="analysis-empty">
      <p class="empty-message">数据不足</p>
      <p class="empty-hint">请添加精灵到队伍后查看分析结果</p>
    </div>
  {/if}

  <!-- Analysis Results -->
  {#if hasData && snapshot}
    <div class="analysis-results">
      <section class="analysis-section">
        <h3>攻向分布</h3>
        {#if Object.keys(snapshot.offensive_distribution).length > 0}
          <div class="distribution-grid">
            {#each Object.entries(snapshot.offensive_distribution) as [type, value]}
              <div class="distribution-item">
                <span class="distribution-label">{type}</span>
                <span class="distribution-value">{value}%</span>
              </div>
            {/each}
          </div>
        {:else}
          <p class="no-data">暂无数据</p>
        {/if}
      </section>

      <section class="analysis-section">
        <h3>攻击覆盖</h3>
        {#if snapshot.attack_coverage.length > 0}
          <div class="tag-list">
            {#each snapshot.attack_coverage as type}
              <span class="tag">{type}</span>
            {/each}
          </div>
        {:else}
          <p class="no-data">暂无数据</p>
        {/if}
      </section>

      <section class="analysis-section">
        <h3>防守侧重点</h3>
        {#if snapshot.defensive_focus.length > 0}
          <div class="tag-list">
            {#each snapshot.defensive_focus as focus}
              <span class="tag">{focus}</span>
            {/each}
          </div>
        {:else}
          <p class="no-data">暂无数据</p>
        {/if}
      </section>

      <section class="analysis-section">
        <h3>抗性较多</h3>
        {#if snapshot.high_resistance.length > 0}
          <div class="tag-list highlight">
            {#each snapshot.high_resistance as type}
              <span class="tag">{type}</span>
            {/each}
          </div>
        {:else}
          <p class="no-data">暂无数据</p>
        {/if}
      </section>

      <section class="analysis-section">
        <h3>易被压制</h3>
        {#if snapshot.weak_against.length > 0}
          <div class="tag-list warning">
            {#each snapshot.weak_against as type}
              <span class="tag">{type}</span>
            {/each}
          </div>
        {:else}
          <p class="no-data">暂无数据</p>
        {/if}
      </section>

      {#if snapshot.metadata}
        <div class="analysis-metadata">
          <span class="metadata-label">分析时间：</span>
          <span class="metadata-value">
            {new Date(snapshot.metadata.analysis_timestamp).toLocaleString('zh-CN')}
          </span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .analysis-view {
    padding: 1rem;
  }

  .analysis-loading,
  .analysis-error,
  .analysis-empty {
    text-align: center;
    padding: 2rem;
    border: 1px dashed #d1d5db;
    border-radius: 0.5rem;
  }

  .error-message {
    color: #dc2626;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .error-hint {
    color: #7f1d1d;
    margin: 0;
    font-size: 0.875rem;
  }

  .empty-message {
    color: #6b7280;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  .empty-hint {
    color: #9ca3af;
    margin: 0;
    font-size: 0.875rem;
  }

  .analysis-results {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .analysis-section {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #f9fafb;
  }

  .analysis-section h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: #1f2937;
    font-weight: 600;
  }

  .distribution-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem;
  }

  .distribution-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background-color: white;
    border-radius: 0.375rem;
  }

  .distribution-label {
    color: #4b5563;
    font-size: 0.875rem;
  }

  .distribution-value {
    font-weight: 600;
    color: #1f2937;
  }

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    background-color: #dbeafe;
    color: #1e40af;
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .tag-list.highlight .tag {
    background-color: #d1fae5;
    color: #065f46;
  }

  .tag-list.warning .tag {
    background-color: #fee2e2;
    color: #991b1b;
  }

  .no-data {
    color: #9ca3af;
    font-style: italic;
    margin: 0;
  }

  .analysis-metadata {
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #6b7280;
  }

  .metadata-label {
    font-weight: 600;
  }
</style>
