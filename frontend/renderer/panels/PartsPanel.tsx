/**
 * PartsPanel.tsx — Project parts list with maturity and problem counts
 *
 * Shows every part in the workspace. The active part row is highlighted;
 * clicking a row calls `onSelectPart` so Viewport/History/Explorer follow.
 *
 * Feature: F-015
 */

/** One part row — data comes from backend parts_list RPC. */
export interface PartListEntry {
  part_id: string;
  name: string;
  maturity: string;
  open_problem_count: number;
}

export interface PartsPanelProps {
  parts: PartListEntry[];
  activePartId: string | null;
  onSelectPart?: (partId: string) => void;
}

/** Turn snake_case maturity (in_review) into readable label (in review). */
function formatMaturity(maturity: string): string {
  return maturity.replace(/_/g, " ");
}

export default function PartsPanel({ parts, activePartId, onSelectPart }: PartsPanelProps) {
  return (
    <div className="parts-panel">
      <div className="panel-placeholder">Parts</div>
      <div className="parts-body">
        {parts.length === 0 ? (
          <div className="parts-empty">
            No parts yet — describe one in chat or use /part.
          </div>
        ) : (
          <ul className="parts-list" role="list">
            {parts.map((part) => {
              const isActive = part.part_id === activePartId;
              return (
                <li key={part.part_id} className="parts-list-item">
                  <button
                    type="button"
                    className={`parts-row ${isActive ? "is-active" : ""}`}
                    aria-selected={isActive}
                    onClick={() => onSelectPart?.(part.part_id)}
                  >
                    <span className="parts-row-name">{part.name}</span>
                    <span className={`parts-maturity parts-maturity-${part.maturity}`}>
                      {formatMaturity(part.maturity)}
                    </span>
                    <span className="parts-problem-count" aria-label="Open problems">
                      {part.open_problem_count}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
