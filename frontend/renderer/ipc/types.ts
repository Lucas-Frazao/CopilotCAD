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

export interface CopilotCADApi {
  ping(): Promise<string>;
  compileIntent(message: string, context?: Record<string, unknown>): Promise<CompileIntentResult>;
  executeIntent(ir: Record<string, unknown>): Promise<ExecuteIntentResult>;
}
