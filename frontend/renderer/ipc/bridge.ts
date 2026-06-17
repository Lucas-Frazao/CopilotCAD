import type {
  CopilotCADApi,
  CompileIntentResult,
  ExecuteIntentResult,
  IntentIRPayload,
} from "./types";

function getApi(): CopilotCADApi {
  if (typeof window === "undefined" || !window.copilotcad) {
    throw new Error("CopilotCAD IPC is only available in the Electron renderer");
  }
  return window.copilotcad;
}

export async function ping(): Promise<string> {
  return getApi().ping();
}

export async function compileIntent(
  message: string,
  context?: Record<string, unknown>,
): Promise<CompileIntentResult> {
  return getApi().compileIntent(message, context);
}

function isExecuteIntentPayload(data: unknown): data is ExecuteIntentResult {
  if (!data || typeof data !== "object") {
    return false;
  }
  const record = data as Record<string, unknown>;
  return typeof record.success === "boolean" && Array.isArray(record.step_ids);
}

/** Backend returns execution payload in JSON-RPC error data when execution fails. */
export async function executeIntent(ir: IntentIRPayload): Promise<ExecuteIntentResult> {
  try {
    const result = await getApi().executeIntent(ir as unknown as Record<string, unknown>);
    return normalizeExecuteResult(result);
  } catch (err) {
    const withData = err as Error & { data?: unknown };
    if (isExecuteIntentPayload(withData.data)) {
      return normalizeExecuteResult(withData.data);
    }
    throw err;
  }
}

function normalizeExecuteResult(raw: unknown): ExecuteIntentResult {
  const record = (raw ?? {}) as Record<string, unknown>;
  const problems = Array.isArray(record.problems) ? (record.problems as ExecuteIntentResult["problems"]) : [];
  return {
    success: Boolean(record.success),
    step_ids: Array.isArray(record.step_ids) ? (record.step_ids as string[]) : [],
    final_step_id: (record.final_step_id as string | null | undefined) ?? null,
    error: (record.error as string | null | undefined) ?? null,
    problems,
  };
}
