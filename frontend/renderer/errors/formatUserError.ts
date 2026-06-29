/**
 * ============================================================================
 * FILE: formatUserError.ts — Turn raw errors into friendly chat messages (F-026)
 * ============================================================================
 *
 * Backend and Electron IPC often throw or return technical error objects.
 * The chat panel calls formatUserError() to convert those into short,
 * actionable sentences a beginner can understand — without leaking stack traces.
 * ============================================================================
 */

/**
 * StructuredErrorData — optional fields the backend attaches to JSON-RPC errors.
 * The "?" on each field means it may be missing.
 */
interface StructuredErrorData {
  error_type?: string;
  message?: string;
  suggested_next_steps?: string[];
  details?: Record<string, unknown>;
}

/**
 * ErrorLike — minimal shape we expect from caught exceptions / IPC failures.
 */
interface ErrorLike {
  message?: string;
  data?: StructuredErrorData;
}

/**
 * formatUserError — main entry: unknown error in, user string out.
 *
 * @param err - Anything thrown or returned from a failed async call.
 * @returns A single string suitable for display in the chat error bubble.
 */
export function formatUserError(err: unknown): string {
  // If err is null, undefined, or a primitive (string/number), stringify directly.
  if (!err || typeof err !== "object") {
    return String(err);
  }

  // Treat err as ErrorLike so we can read .message and .data safely.
  const e = err as ErrorLike;
  const data = e.data;
  // Default to empty array if backend did not suggest recovery steps.
  const steps = data?.suggested_next_steps ?? [];

  // Validation: LLM/compile could not build a modeling plan from the prompt.
  if (data?.error_type === "validation") {
    return (
      "I couldn't turn that into a modeling plan. Try describing a part with dimensions — " +
      'for example: "Create a 100×50×6 mm plate with 6 mm corner holes."'
    );
  }
  // Configuration: API key or adapter setup missing.
  if (data?.error_type === "configuration") {
    return "LLM is not configured. Set ANTHROPIC_API_KEY in your environment and restart the app.";
  }
  // Export: user tried to export before any geometry existed.
  if (data?.error_type === "export") {
    return "This part has no geometry yet. Model the part in chat first, then export again.";
  }
  // Slash command syntax or handler rejection.
  if (data?.error_type === "slash") {
    return data.message ?? "Invalid slash command. Check usage and try again.";
  }
  // Execution or kernel geometry failure — may include bullet-point next steps.
  if (data?.error_type === "execution" || data?.error_type === "geometry") {
    const base = data.message ?? "Geometry generation failed.";
    if (steps.length === 0) {
      return base;
    }
    // Join each suggested step as a markdown-style bullet line.
    return `${base}\n${steps.map((s) => `• ${s}`).join("\n")}`;
  }

  // Fallback: use exception message or String(err).
  const raw = e.message ?? String(err);
  // Electron wraps IPC failures in a generic remote-method error string.
  if (raw.includes("Error invoking remote method")) {
    return "Something went wrong talking to the backend. Try restarting the app.";
  }

  // Last resort: structured message from data, else raw message.
  return data?.message ?? raw;
}
