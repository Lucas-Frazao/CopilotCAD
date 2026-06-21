/** JSON-RPC and backend payload types for renderer IPC (F-007 / F-008). */

export interface JsonRpcErrorData {
  error_type?: string;
  message?: string;
  details?: Record<string, unknown>;
  field_errors?: unknown[];
}

export interface IntentIRTarget {
  part_id?: string | null;
  assembly_id?: string | null;
  doc_path?: string | null;
}

export interface IRAssumptionPayload {
  id: string;
  text: string;
  scope?: string;
  source?: string;
  importance?: "low" | "medium" | "high";
  status?: "proposed" | "confirmed" | "rejected";
}

export interface IRQuestionPayload {
  id: string;
  text: string;
  blocking?: boolean;
  status?: "open" | "answered" | "dismissed";
  answer?: string | null;
}

/** Subset of backend Intent IR returned by compile_intent. */
export interface IntentIRPayload {
  type: string;
  prompt: string;
  summary: string;
  target: IntentIRTarget;
  steps?: unknown[];
  assumptions?: IRAssumptionPayload[];
  questions?: IRQuestionPayload[];
  constraints?: Record<string, unknown>;
  links?: Record<string, unknown>;
}

export type CompileIntentResult = IntentIRPayload;

export interface ProblemPayload {
  id: string;
  type: string;
  severity: "warning" | "error" | "blocking";
  message: string;
  part_id?: string | null;
  step_id?: string | null;
  suggested_next_steps?: string[];
}

export interface ExecuteIntentResult {
  success: boolean;
  step_ids: string[];
  final_step_id?: string | null;
  error?: string | null;
  problems: ProblemPayload[];
}

/**
 * Result envelope returned by the main process for every backend RPC. Unlike a
 * thrown error, a plain object survives Electron's structured-clone IPC intact, so
 * the JSON-RPC `code`/`data` reach the renderer without string-encoding hacks.
 */
export type RpcEnvelope<T> =
  | { ok: true; value: T }
  | { ok: false; error: { message: string; code?: number; data?: unknown } };

/** Backend health as reported by the main process. */
export type BackendStatus = "starting" | "ready" | "down";

export interface CopilotCADApi {
  ping(): Promise<RpcEnvelope<string>>;
  getWorkspacePath(): Promise<string>;
  getBackendStatus(): Promise<BackendStatus>;
  /** Subscribe to backend status changes; returns an unsubscribe function. */
  onBackendStatus(callback: (status: BackendStatus) => void): () => void;
  compileIntent(
    message: string,
    context?: Record<string, unknown>,
  ): Promise<RpcEnvelope<CompileIntentResult>>;
  executeIntent(ir: Record<string, unknown>): Promise<RpcEnvelope<ExecuteIntentResult>>;
  listWorkspaceTree(workspacePath: string): Promise<RpcEnvelope<WorkspaceTreeNode[]>>;
  readWorkspaceFile(
    workspacePath: string,
    relativePath: string,
  ): Promise<RpcEnvelope<WorkspaceFileContents>>;
}

/** Workspace explorer tree node (F-009). */
export interface WorkspaceTreeNode {
  name: string;
  path: string;
  type: "file" | "dir";
  children?: WorkspaceTreeNode[];
}

export interface WorkspaceFileContents {
  contents: string;
}
