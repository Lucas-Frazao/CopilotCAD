import { buildDiffSummaryText } from "../chat/chat-utils";
import type { ExecuteIntentResult } from "../ipc/types";

interface DiffSummaryProps {
  execution: ExecuteIntentResult;
}

export default function DiffSummary({ execution }: DiffSummaryProps) {
  return (
    <div className={`diff-summary ${execution.success ? "diff-summary-success" : "diff-summary-error"}`}>
      <div className="diff-summary-label">Diff</div>
      <div className="diff-summary-text">{buildDiffSummaryText(execution)}</div>
    </div>
  );
}
