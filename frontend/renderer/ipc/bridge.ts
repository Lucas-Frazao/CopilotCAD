import type {
  CopilotCADApi,
  CompileIntentResult,
  ExecuteIntentResult,
  IntentIRPayload,
  WorkspaceFileContents,
  WorkspaceTreeNode,
} from "./types";

const RPC_ERROR_PREFIX = "COPILOTCAD_RPC:";

function getApi(): CopilotCADApi {
  if (typeof window === "undefined" || !window.copilotcad) {
    throw new Error("CopilotCAD IPC is only available in the Electron renderer");
  }
  return window.copilotcad;
}

function extractRpcPayload(message: string): {
  message?: string;
  code?: number;
  data?: unknown;
} | null {
  const marker = RPC_ERROR_PREFIX;
  const index = message.indexOf(marker);
  if (index === -1) {
    return null;
  }

  try {
    return JSON.parse(message.slice(index + marker.length)) as {
      message?: string;
      code?: number;
      data?: unknown;
    };
  } catch {
    return null;
  }
}

function normalizeIpcError(err: unknown): Error {
  if (err instanceof Error) {
    const rpcPayload = extractRpcPayload(err.message);
    if (rpcPayload) {
      const normalized = new Error(rpcPayload.message ?? "Request failed");
      (normalized as Error & { code?: number; data?: unknown }).code = rpcPayload.code;
      (normalized as Error & { data?: unknown }).data = rpcPayload.data;
      return normalized;
    }

    if (err.message.startsWith(RPC_ERROR_PREFIX)) {
      try {
        const payload = JSON.parse(err.message.slice(RPC_ERROR_PREFIX.length)) as {
          message?: string;
          code?: number;
          data?: unknown;
        };
        const normalized = new Error(payload.message ?? "Request failed");
        (normalized as Error & { code?: number; data?: unknown }).code = payload.code;
        (normalized as Error & { data?: unknown }).data = payload.data;
        return normalized;
      } catch {
        return err;
      }
    }

    if (err.message.includes("Intent IR validation failed")) {
      const normalized = new Error("Intent IR validation failed");
      (normalized as Error & { data?: unknown }).data = {
        error_type: "validation",
        message: "Intent IR validation failed",
      };
      return normalized;
    }

    return err;
  }

  return new Error(String(err));
}

export async function ping(): Promise<string> {
  return getApi().ping();
}

export async function compileIntent(
  message: string,
  context?: Record<string, unknown>,
): Promise<CompileIntentResult> {
  try {
    return await getApi().compileIntent(message, context);
  } catch (err) {
    throw normalizeIpcError(err);
  }
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
    const normalized = normalizeIpcError(err);
    const withData = normalized as Error & { data?: unknown };
    if (isExecuteIntentPayload(withData.data)) {
      return normalizeExecuteResult(withData.data);
    }
    throw normalized;
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
  const api = getApi() as CopilotCADApi & { getWorkspacePath?: () => Promise<string> };
  if (typeof api.getWorkspacePath !== "function") {
    throw new Error("Workspace path is not available in this environment");
  }
  return api.getWorkspacePath();
}

export async function listWorkspaceTree(
  workspacePath: string,
): Promise<WorkspaceTreeNode[]> {
  try {
    return await getApi().listWorkspaceTree(workspacePath);
  } catch (err) {
    throw normalizeIpcError(err);
  }
}

export async function readWorkspaceFile(
  workspacePath: string,
  relativePath: string,
): Promise<WorkspaceFileContents> {
  try {
    return await getApi().readWorkspaceFile(workspacePath, relativePath);
  } catch (err) {
    throw normalizeIpcError(err);
  }
}
