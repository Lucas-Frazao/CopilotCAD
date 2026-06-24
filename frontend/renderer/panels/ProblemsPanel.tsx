import { useMemo } from "react";

import ProblemItem from "../components/ProblemItem";
import type { ProblemPayload } from "../ipc/types";

const SEVERITY_ORDER: Record<string, number> = {
  blocking: 0,
  error: 1,
  warning: 2,
};

export interface ProblemsPanelProps {
  problems: ProblemPayload[];
  onNavigate?: (problem: ProblemPayload) => void;
}

function sortBySeverity(problems: ProblemPayload[]): ProblemPayload[] {
  return [...problems].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99),
  );
}

export default function ProblemsPanel({ problems, onNavigate }: ProblemsPanelProps) {
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