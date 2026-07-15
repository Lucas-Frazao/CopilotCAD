/**
 * ============================================================================
 * FILE: DiffSummary.tsx — Shows execution outcome summary in chat (diff block)
 * ============================================================================
 *
 * After the backend runs a modeling plan, the chat shows a compact "Diff" box
 * with how many steps ran and whether it succeeded. This component delegates
 * text formatting to buildDiffSummaryText in chat-utils.ts.
 * ============================================================================
 */

import { buildDiffSummaryText } from "../chat/chat-utils";
import type { ExecuteIntentResult } from "../ipc/types";

/** Only prop: the execute_intent result object from the last chat action. */
interface DiffSummaryProps {
  execution: ExecuteIntentResult;
}

/**
 * DiffSummary — styled div with success/error CSS class from execution.success.
 */
export default function DiffSummary({ execution }: DiffSummaryProps) {
  return (
    <div className={`diff-summary ${execution.success ? "diff-summary-success" : "diff-summary-error"}`}>
      <div className="diff-summary-label">Diff</div>
      <div className="diff-summary-text">{buildDiffSummaryText(execution)}</div>
    </div>
  );
}
