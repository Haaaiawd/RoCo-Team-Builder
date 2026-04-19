/**
 * Team Workbench Host Component
 * 
 * Implements dual entry workbench host with handoff fallback.
 * Corresponds to web-ui-system.md §4.2 Core Components - Team Workbench Host
 * 
 * Entry points:
 * 1. Sidebar entry - loads cached draft or creates empty draft
 * 2. Agent handoff entry - loads from handoff payload or falls back to empty draft
 */

import React, { useState, useEffect } from "react";
import type { TeamDraft, WorkbenchHandOffPayload, TeamWorkbenchUiState } from "./types";
import { hydrateWorkbenchFromEntry, saveDraft, clearDraft } from "./hydration";

interface WorkbenchHostProps {
  entryPoint: "sidebar" | "agent_handoff";
  handoffPayload: WorkbenchHandOffPayload | null;
}

/**
 * Workbench Host Component
 * 
 * Manages team draft state and provides workbench entry points.
 * Handles handoff failure with empty draft fallback.
 */
export function WorkbenchHost({ entryPoint, handoffPayload }: WorkbenchHostProps) {
  const [draft, setDraft] = useState<TeamDraft | null>(null);
  const [uiState, setUiState] = useState<TeamWorkbenchUiState>({
    handoff_status: "idle",
    analysis_status: "idle",
    ai_review_status: "idle",
    import_status: "idle",
    export_status: "idle",
    dirty: false,
    last_error_code: null,
  });
  const [hydrationError, setHydrationError] = useState<string | null>(null);

  useEffect(() => {
    // Hydrate draft from entry point
    setUiState((prev) => ({ ...prev, handoff_status: "hydrating" }));
    
    const { draft: hydratedDraft, error } = hydrateWorkbenchFromEntry(entryPoint, handoffPayload);
    
    setDraft(hydratedDraft);
    setHydrationError(error);
    
    if (error) {
      setUiState((prev) => ({ 
        ...prev, 
        handoff_status: "failed",
        last_error_code: error
      }));
    } else {
      setUiState((prev) => ({ 
        ...prev, 
        handoff_status: "ready"
      }));
    }
  }, [entryPoint, handoffPayload]);

  const handleClearDraft = () => {
    clearDraft();
    setDraft(null);
    setHydrationError(null);
  };

  const handleSaveDraft = () => {
    if (draft) {
      saveDraft(draft);
      setUiState((prev) => ({ ...prev, dirty: false }));
    }
  };

  // Render workbench UI
  return (
    <div className="workbench-host">
      {/* Hydration Error Display */}
      {hydrationError && (
        <div className="hydration-error-banner">
          <p className="error-message">
            {hydrationError === "HANDOFF_PAYLOAD_INVALID" 
              ? "无法加载队伍草稿：承接载荷缺失或损坏"
              : hydrationError === "HANDOFF_SCHEMA_VERSION_MISMATCH"
              ? "无法加载队伍草稿：数据版本不匹配"
              : "无法加载队伍草稿，已为您创建空白草稿"
            }
          </p>
          <p className="error-hint">您可以继续编辑空白草稿或从侧边栏重新进入工作台</p>
        </div>
      )}

      {/* Workbench Content */}
      {draft && (
        <div className="workbench-content">
          <header className="workbench-header">
            <h1>配队工作台</h1>
            <div className="draft-meta">
              <span className="draft-source">
                {draft.source === "agent_handoff" ? "来自 Agent 推荐" : "空白草稿"}
              </span>
              {uiState.dirty && (
                <span className="dirty-indicator">未保存</span>
              )}
            </div>
          </header>

          {/* Draft Slots */}
          <section className="draft-slots">
            <h2>队伍配置</h2>
            {draft.slots.length === 0 ? (
              <p className="empty-draft-hint">暂无精灵配置，请添加精灵</p>
            ) : (
              <div className="slots-grid">
                {draft.slots.map((slot) => (
                  <div key={slot.slot_index} className="slot-card">
                    <div className="slot-number">槽位 {slot.slot_index + 1}</div>
                    {slot.spirit_name ? (
                      <div className="slot-content">
                        <div className="spirit-name">{slot.spirit_name}</div>
                        {slot.skill_names.length > 0 && (
                          <div className="skill-list">
                            {slot.skill_names.map((skill, idx) => (
                              <span key={idx} className="skill-tag">{skill}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="slot-empty">空槽位</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Action Bar */}
          <footer className="workbench-actions">
            <button 
              className="action-button"
              onClick={handleSaveDraft}
              disabled={!uiState.dirty}
            >
              保存草稿
            </button>
            <button 
              className="action-button secondary"
              onClick={handleClearDraft}
            >
              清空草稿
            </button>
          </footer>
        </div>
      )}

      {/* Loading State */}
      {uiState.handoff_status === "hydrating" && (
        <div className="loading-state">
          <p>正在加载工作台...</p>
        </div>
      )}
    </div>
  );
}
