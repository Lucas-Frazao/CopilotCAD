/**
 * ============================================================================
 * FILE: chat-types.ts — Type definitions for chat messages and question UI
 * ============================================================================
 *
 * TypeScript "types" describe the shape of data — like labels on boxes saying
 * what must be inside. They do not exist at runtime; they help the compiler
 * catch mistakes (e.g. using the wrong message kind).
 *
 * This file defines what a chat message looks like in CopilotCAD's chat panel
 * and how follow-up "question" UI tracks user answers.
 * ============================================================================
 */

// "import type" pulls in only type information (no runtime JavaScript).
// ExecuteIntentResult and IntentIRPayload come from the IPC types module —
// they describe backend responses after compiling/executing user intent.
import type { ExecuteIntentResult, IntentIRPayload } from "../ipc/types";

/**
 * ChatMessageKind — discriminates different assistant message render modes.
 *
 * - text: plain markdown/text reply
 * - compile_result: shows intent + execution outcome
 * - error: shows a formatted error string
 * - slash_hint: hints for /commands
 * - approval_required: risky action needs user approval (F-022)
 */
export type ChatMessageKind =
  | "text"
  | "compile_result"
  | "error"
  | "slash_hint"
  | "approval_required";

/**
 * ChatMessageData — one row in the chat transcript (user or assistant).
 */
export interface ChatMessageData {
  // Unique id for React list keys and updates.
  id: string;
  // Who sent it: the human user or the assistant (app/LLM).
  role: "user" | "assistant";
  // Which renderer variant to use in ChatMessage.tsx.
  kind: ChatMessageKind;
  // Optional plain text body (most kinds use this).
  text?: string;
  // When kind is approval_required, links to backend pending approval record.
  pendingId?: string;
  // Structured modeling plan from compile step (Intent IR).
  intent?: IntentIRPayload;
  // Result of running that plan on the CAD kernel.
  execution?: ExecuteIntentResult;
}

/**
 * QuestionLocalState — UI-only state for an inline question the assistant asked.
 */
export interface QuestionLocalState {
  // open: waiting for answer; answered: user submitted; dismissed: user closed it.
  status: "open" | "answered" | "dismissed";
  // The user's typed answer text.
  answer: string;
}
