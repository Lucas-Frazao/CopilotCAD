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

/** Greetings and small talk — skip compile_intent and reply locally. */
export function isConversationalMessage(text: string): boolean {
  const normalized = text.trim().toLowerCase().replace(/[!?.]+$/, "");
  return /^(hi|hello|hey|thanks|thank you|yo|good morning|good afternoon)$/.test(normalized);
}

export const CONVERSATIONAL_REPLY =
  "Hi! Describe a part you'd like to create — for example, a 100×50 mm mounting plate with 6 mm corner holes — or ask about your project.";

interface CompileErrorData {
  error_type?: string;
  message?: string;
  details?: {
    message?: string;
    field_errors?: Array<{ loc?: unknown[]; msg?: string }>;
    invalid_ops?: string[];
  };
}

/** User-facing compile error text from JSON-RPC error payloads. */
export function formatCompileError(err: unknown): string {
  if (!(err instanceof Error)) {
    return String(err);
  }

  const withData = err as Error & { data?: CompileErrorData };
  const data = withData.data;

  if (data?.error_type === "validation") {
    return (
      "I couldn't turn that into a modeling plan. Try describing a part with dimensions — " +
      "for example: \"Create a 100×50×6 mm plate with 6 mm corner holes.\""
    );
  }
  if (data?.error_type === "configuration") {
    return "LLM is not configured. Set ANTHROPIC_API_KEY in your environment and restart the app.";
  }
  if (data?.error_type === "parse") {
    return "The model returned an invalid response. Please try again or rephrase your request.";
  }
  if (data?.message) {
    return data.message;
  }

  return withData.message;
}
