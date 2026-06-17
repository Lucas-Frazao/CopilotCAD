/** JSON-RPC and backend payload types for renderer IPC (F-007). */

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

/** Subset of backend Intent IR returned by compile_intent. */
export interface IntentIRPayload {
  type: string;
  prompt: string;
  summary: string;
  target: IntentIRTarget;
  steps?: unknown[];
  assumptions?: unknown[];
  questions?: unknown[];
  constraints?: Record<string, unknown>;
  links?: Record<string, unknown>;
}

export type CompileIntentResult = IntentIRPayload;

export interface CopilotCADApi {
  ping(): Promise<string>;
  compileIntent(message: string, context?: Record<string, unknown>): Promise<CompileIntentResult>;
}
