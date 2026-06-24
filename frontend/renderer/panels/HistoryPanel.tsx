import { useState } from "react";

export interface HistoryActionEntry {
  id: string;
  timestamp: string;
  type: string;
  summary: string;
  step_ids?: string[];
  message_id?: string;
}

export interface HistoryFeatureEntry {
  id: string;
  op: string;
  label: string;
}

export interface HistoryPanelProps {
  partId: string;
  actions: HistoryActionEntry[];
  features: HistoryFeatureEntry[];
  onOpenChatMessage?: (messageId: string) => void;
  initialTab?: "actions" | "features";
}

type HistoryTab = "actions" | "features";

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  return date.toLocaleString();
}

export default function HistoryPanel({
  partId,
  actions,
  features,
  onOpenChatMessage,
  initialTab = "actions",
}: HistoryPanelProps) {
  const [activeTab, setActiveTab] = useState<HistoryTab>(initialTab);

  return (
    <div className="history-panel" data-part-id={partId}>
      <div className="panel-placeholder">History</div>
      <div className="history-tabs" role="tablist" aria-label="History views">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "actions"}
          className={`history-tab ${activeTab === "actions" ? "is-active" : ""}`}
          onClick={() => setActiveTab("actions")}
        >
          Actions
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "features"}
          className={`history-tab ${activeTab === "features" ? "is-active" : ""}`}
          onClick={() => setActiveTab("features")}
        >
          Features
        </button>
      </div>
      <div className="history-body">
        {activeTab === "actions" ? (
          actions.length === 0 ? (
            <div className="history-empty">No actions recorded for this part.</div>
          ) : (
            <ul className="history-actions-list" role="list">
              {actions.map((entry) => (
                <li key={entry.id} className="history-action-item">
                  <div className="history-action-summary">{entry.summary}</div>
                  <div className="history-action-timestamp">{formatTimestamp(entry.timestamp)}</div>
                  {entry.message_id && onOpenChatMessage && (
                    <button
                      type="button"
                      className="history-open-chat"
                      onClick={() => onOpenChatMessage(entry.message_id!)}
                    >
                      Open in chat
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )
        ) : features.length === 0 ? (
          <div className="history-empty">No modeling features yet.</div>
        ) : (
          <ul className="history-features-list" role="list">
            {features.map((entry) => (
              <li key={entry.id} className="history-feature-item">
                {entry.label}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}