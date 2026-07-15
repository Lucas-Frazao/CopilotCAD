/**
 * ProblemsPanel.tsx — Validation and blocking issues list
 *
 * Surfaces problems from the backend problems engine (unresolved assumptions,
 * missing inputs, interface conflicts, etc.). Blocking items sort to the top.
 * Clicking a row can navigate the user to the relevant part or chat context.
 *
 * Feature: F-010
 */

import { useMemo } from "react";

// Shared row component — shows severity badge, message, suggested next steps.
import ProblemItem from "../components/ProblemItem";
import type { ProblemPayload } from "../ipc/types";

/** Lower number = higher priority in the sorted list. */
const SEVERITY_ORDER: Record<string, number> = {
  blocking: 0,
  error: 1,
  warning: 2,
};

export interface ProblemsPanelProps {
  problems: ProblemPayload[];
  onNavigate?: (problem: ProblemPayload) => void;
}

/** Stable sort: blocking first, then error, then warning; unknown severities last. */
function sortBySeverity(problems: ProblemPayload[]): ProblemPayload[] {
  return [...problems].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99),
  );
}

export default function ProblemsPanel({ problems, onNavigate }: ProblemsPanelProps) {
  // Re-sort only when the problems array reference/content changes.
  const sorted = useMemo(() => sortBySeverity(problems), [problems]);

  return (
    <div className="problems-panel">
      <div className="panel-placeholder">Problems</div>
      <div className="problems-body">
        {sorted.length === 0 ? (
          <div className="problems-empty">No problems — you're all set.</div>
        ) : (
          <ul className="problems-list" role="list">
            {sorted.map((problem) => (
              <ProblemItem
                key={problem.id}
                problem={problem}
                onClick={onNavigate}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
