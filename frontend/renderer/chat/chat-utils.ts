import type { ExecuteIntentResult } from "../ipc/types";

/** One-line execution summary for diff display and tests. */
export function buildDiffSummaryText(execution: ExecuteIntentResult): string {
  if (execution.success) {
    const steps =
      execution.step_ids.length > 0 ? execution.step_ids.join(", ") : "none";
    const final = execution.final_step_id ?? "none";
    return `Executed ${execution.step_ids.length} step(s): ${steps}. Final step: ${final}.`;
  }

  const detail = execution.error ?? "Execution failed";
  const steps =
    execution.step_ids.length > 0 ? execution.step_ids.join(", ") : "none";
  return `Execution failed: ${detail}. Steps attempted: ${steps}.`;
}

export const SLASH_COMMANDS = [
  "/vision",
  "/constitution",
  "/architecture",
  "/manufacturing",
  "/part",
  "/interface",
  "/plan",
  "/review",
  "/release",
  "/export",
  "/assumptions",
  "/history",
] as const;

export function filterSlashCommands(input: string): string[] {
  const trimmed = input.trim();
  if (!trimmed.startsWith("/")) {
    return [];
  }
  const lower = trimmed.toLowerCase();
  return SLASH_COMMANDS.filter((cmd) => cmd.startsWith(lower));
}

export function isSlashOnlyMessage(text: string): boolean {
  const trimmed = text.trim().toLowerCase();
  if (!trimmed.startsWith("/")) {
    return false;
  }
  return SLASH_COMMANDS.some((cmd) => trimmed === cmd);
}
