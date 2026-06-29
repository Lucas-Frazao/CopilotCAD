/**
 * ============================================================================
 * FILE: bridge.ts — Renderer-side IPC facade to the Electron main process
 * ============================================================================
 *
 * React components must not call window.copilotcad directly everywhere — this
 * module centralizes access, unwraps RpcEnvelope results, and normalizes edge
 * cases (e.g. execute_intent returning failure data inside JSON-RPC errors).
 * ============================================================================
 */

// Type-only imports from our IPC contract definitions.
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
import type { PartMeshPayload } from "./mesh-types";

/**
 * getApi — return the preload-exposed API or throw if not in Electron renderer.
 */
function getApi(): CopilotCADApi {
  // SSR/tests may have no window; desktop preload must attach window.copilotcad.
  if (typeof window === "undefined" || !window.copilotcad) {
    throw new Error("CopilotCAD IPC is only available in the Electron renderer");
  }
  return window.copilotcad;
}

/**
 * unwrap — convert RpcEnvelope to value or throw Error with code/data attached.
 *
 * Replaces an older hack that JSON-stringified errors into Error.message.
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

/** Health check RPC — verifies main ↔ backend path works. */
export async function ping(): Promise<string> {
  return unwrap(await getApi().ping());
}

/** Send user message to backend LLM compile_intent. */
export async function compileIntent(
  message: string,
  context?: Record<string, unknown>,
): Promise<CompileIntentResult> {
  return unwrap(await getApi().compileIntent(message, context));
}

/** Type guard: does unknown value look like ExecuteIntentResult? */
function isExecuteIntentPayload(data: unknown): data is ExecuteIntentResult {
  if (!data || typeof data !== "object") {
    return false;
  }
  const record = data as Record<string, unknown>;
  return typeof record.success === "boolean" && Array.isArray(record.step_ids);
}

/**
 * executeIntent — run compiled IR on the backend for the current workspace.
 *
 * On execution failure the backend may put the full result in error.data; we
 * return that as a normal ExecuteIntentResult so chat can show problems/diff.
 */
export async function executeIntent(ir: IntentIRPayload): Promise<ExecuteIntentResult> {
  const workspacePath = await getWorkspacePath();
  try {
    const value = unwrap(
      await getApi().executeIntent(ir as unknown as Record<string, unknown>, workspacePath),
    );
    return normalizeExecuteResult(value);
  } catch (err) {
    const withData = err as Error & { data?: unknown };
    if (isExecuteIntentPayload(withData.data)) {
      return normalizeExecuteResult(withData.data);
    }
    throw err;
  }
}

/** Coerce partial/unknown RPC payloads into a strict ExecuteIntentResult. */
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

/** Fetch tessellated mesh for viewport rendering. */
export async function getPartMesh(
  workspacePath: string,
  partId: string,
): Promise<PartMeshPayload> {
  return unwrap(await getApi().getPartMesh(workspacePath, partId));
}

/** Absolute path to the open .copilotcad workspace on disk. */
export async function getWorkspacePath(): Promise<string> {
  return getApi().getWorkspacePath();
}

/** Current Python backend process status. */
export async function getBackendStatus(): Promise<BackendStatus> {
  return getApi().getBackendStatus();
}

/** Subscribe to backend status push events from main process. */
export function onBackendStatus(callback: (status: BackendStatus) => void): () => void {
  return getApi().onBackendStatus(callback);
}

/** Explorer panel: list files/folders under workspace root. */
export async function listWorkspaceTree(workspacePath: string): Promise<WorkspaceTreeNode[]> {
  return unwrap(await getApi().listWorkspaceTree(workspacePath));
}

/** Read a text file from the workspace (relative path). */
export async function readWorkspaceFile(
  workspacePath: string,
  relativePath: string,
): Promise<WorkspaceFileContents> {
  return unwrap(await getApi().readWorkspaceFile(workspacePath, relativePath));
}

/** Update assumption status on a part (optional API on newer preloads). */
export async function updateAssumption(
  partId: string,
  assumptionId: string,
  status: "proposed" | "confirmed" | "rejected",
  text?: string,
): Promise<unknown> {
  const api = getApi() as CopilotCADApi & {
    updateAssumption?: (
      partId: string,
      assumptionId: string,
      status: string,
      text?: string,
    ) => Promise<RpcEnvelope<unknown>>;
  };
  if (!api.updateAssumption) {
    throw new Error("updateAssumption is not available in this environment");
  }
  return unwrap(await api.updateAssumption(partId, assumptionId, status, text));
}
