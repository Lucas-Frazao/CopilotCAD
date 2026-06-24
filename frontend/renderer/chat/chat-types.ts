import type { ExecuteIntentResult, IntentIRPayload } from "../ipc/types";

export type ChatMessageKind =
  | "text"
  | "compile_result"
  | "error"
  | "slash_hint"
  | "approval_required";

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  kind: ChatMessageKind;
  text?: string;
  pendingId?: string;
  intent?: IntentIRPayload;
  execution?: ExecuteIntentResult;
}

export interface QuestionLocalState {
  status: "open" | "answered" | "dismissed";
  answer: string;
}
