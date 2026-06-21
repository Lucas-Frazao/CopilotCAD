import type {
  BackendStatus,
  CopilotCADApi,
  CompileIntentResult,
  ExecuteIntentResult,
  IntentIRPayload,
  RpcEnvelope,
  WorkspaceFileContents,
  WorkspaceTreeNode,
} from "./types";

function getApi(): CopilotCADApi {
  if (typeof window === "undefined" || !window.copilotcad) {
    throw new Error("CopilotCAD IPC is only available in the Electron renderer");
  }
  return window.copilotcad;
}

/**
 * Unwrap a backend RPC envelope: return the value on success, or throw an Error
 * carrying the original JSON-RPC `code`/`data` on failure. Replaces the previous
 * brittle approach of stuffing JSON into an Error message behind a magic prefix.
 */
function unwrap<T>(envelope: RpcEnvelope<T>): T {
  if (envelope.ok) {
    return envelope.value;
  }
  const error = new Error(envelope.error.message) as Error & { code?: number; data?: unknown };
  error.code = envelope.error.code;
  error.data = envelope.error.data;
  throw error;
}

export async function ping(): Promise<string> {
  return unwrap(await getApi().ping());
}

export async function compileIntent(
  message: string,
  context?: Record<string, unknown>,
): Promise<CompileIntentResult> {
  return unwrap(await getApi().compileIntent(message, context));
}

function isExecuteIntentPayload(data: unknown): data is ExecuteIntentResult {
  if (!data || typeof data !== "object") {
    return false;
  }
  const record = data as Record<string, unknown>;
  return typeof record.success === "boolean" && Array.isArray(record.step_ids);
}

/**
 * Execute a compiled IR. On an execution failure the backend returns the full
 * execution payload (steps + problems) as the JSON-RPC error `data`; we surface
 * that as a normal result so the chat panel can render the diff + problems.
 */
export async function executeIntent(ir: IntentIRPayload): Promise<ExecuteIntentResult> {
  try {
    const value = unwrap(await getApi().executeIntent(ir as unknown as Record<string, unknown>));
    return normalizeExecuteResult(value);
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

export async function getWorkspacePath(): Promise<string> {
  return getApi().getWorkspacePath();
}

export async function getBackendStatus(): Promise<BackendStatus> {
  return getApi().getBackendStatus();
}

export function onBackendStatus(callback: (status: BackendStatus) => void): () => void {
  return getApi().onBackendStatus(callback);
}

export async function listWorkspaceTree(workspacePath: string): Promise<WorkspaceTreeNode[]> {
  return unwrap(await getApi().listWorkspaceTree(workspacePath));
}

export async function readWorkspaceFile(
  workspacePath: string,
  relativePath: string,
): Promise<WorkspaceFileContents> {
  return unwrap(await getApi().readWorkspaceFile(workspacePath, relativePath));
}
