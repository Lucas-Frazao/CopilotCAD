/**
 * ChatPanel.tsx — Main chat sidebar for CopilotCAD
 *
 * This panel is where users type natural-language CAD requests, slash commands,
 * and questions. Messages flow through three paths:
 *   1. Slash-only commands → local hint (F-014 handlers live elsewhere)
 *   2. Conversational text (hello, thanks) → canned reply, no backend call
 *   3. Modeling intent → compileIntent → executeIntent → sync project state
 *
 * Parent components pass `onWorkspaceChanged` so Explorer/Parts/Viewport
 * panels refresh after a successful execute.
 */

// React hooks: useState holds component state; KeyboardEvent types the key handler.
import { useState, type KeyboardEvent } from "react";

// Shared chat types — shapes for messages and per-question UI state.
import type { ChatMessageData, QuestionLocalState } from "../chat/chat-types";
// Pure helpers: slash filtering, message classification, error formatting.
import { filterSlashCommands, isSlashOnlyMessage, isConversationalMessage, CONVERSATIONAL_REPLY, formatCompileError } from "../chat/chat-utils";
// Renders a single bubble (text, compile result, approval, etc.).
import ChatMessage from "../components/ChatMessage";
// Dropdown shown when the user types "/" — lists matching slash commands.
import SlashCommandPicker from "../components/SlashCommandPicker";
// IPC bridge: talks to the Python backend over JSON-RPC (stdio in Electron).
import { compileIntent, executeIntent } from "../ipc/bridge";
// After execute, updates in-memory project state so other panels stay in sync.
import { syncProjectStateAfterExecute } from "../project/syncAfterExecute";

/**
 * Unique message IDs without collisions.
 * Date.now() failed when two messages were created in the same millisecond
 * (e.g. user turn + immediate local reply), producing duplicate React keys.
 */
let messageSeq = 0;
function nextMessageId(prefix: string): string {
  messageSeq += 1;
  return `${prefix}-${messageSeq}`;
}

/** First message shown when the panel mounts — no backend call needed. */
const WELCOME: ChatMessageData = {
  id: "welcome",
  role: "assistant",
  kind: "text",
  text: "What to do first? Ask about this CAD model or we can start creating one.",
};

export default function ChatPanel({
  onWorkspaceChanged,
}: {
  /** Optional callback fired after a successful execute so sibling panels refetch. */
  onWorkspaceChanged?: () => void;
}) {
  // --- Local UI state ---
  const [messages, setMessages] = useState<ChatMessageData[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false); // true while compile/execute is in flight
  const [pickerIndex, setPickerIndex] = useState(0); // highlighted row in slash picker
  const [questionStates, setQuestionStates] = useState<Record<string, QuestionLocalState>>({});

  // Derive slash picker visibility from current input text.
  const slashMatches = filterSlashCommands(input);
  const showPicker = input.startsWith("/") && slashMatches.length > 0;

  /** Insert chosen slash command into the input and reset picker highlight. */
  const selectSlashCommand = (command: string) => {
    setInput(`${command} `);
    setPickerIndex(0);
  };

  /** Track typed answer for an open clarification question (before Accept). */
  const updateQuestionAnswer = (questionId: string, answer: string) => {
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        status: prev[questionId]?.status ?? "open",
        answer,
      },
    }));
  };

  /** Mark a clarification question as answered (locks in the current answer). */
  const acceptQuestion = (questionId: string) => {
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        status: "answered",
        answer: prev[questionId]?.answer ?? "",
      },
    }));
  };

  /**
   * Main send pipeline: append user bubble, then route by message kind.
   * Async because compile + execute hit the Python backend.
   */
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) {
      return; // ignore empty sends and double-clicks while busy
    }

    const userMessage: ChatMessageData = {
      id: nextMessageId("user"),
      role: "user",
      kind: "text",
      text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    // Path 1: bare slash command with no arguments — show stub hint locally.
    if (isSlashOnlyMessage(text)) {
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant-slash"),
          role: "assistant",
          kind: "slash_hint",
          text: "Slash command recognized (handler not implemented until F-014).",
        },
      ]);
      setSending(false);
      return;
    }

    // Path 2: greetings / small talk — no LLM or kernel work.
    if (isConversationalMessage(text)) {
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant-chat"),
          role: "assistant",
          kind: "text",
          text: CONVERSATIONAL_REPLY,
        },
      ]);
      setSending(false);
      return;
    }

    // Path 3: modeling intent — compile → execute → sync → show result bubble.
    try {
      const intent = await compileIntent(text);
      const execution = await executeIntent(intent);
      await syncProjectStateAfterExecute(intent, execution);
      if (execution.success) {
        onWorkspaceChanged?.(); // notify App shell to bump refresh tokens
      }
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant"),
          role: "assistant",
          kind: "compile_result",
          intent,
          execution,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId("assistant-error"),
          role: "assistant",
          kind: "error",
          text: formatCompileError(err),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  /** Enter sends (or picks slash command); arrows navigate the slash picker. */
  const handleInputKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (showPicker && slashMatches.length > 0) {
        const command = slashMatches[pickerIndex] ?? slashMatches[0];
        selectSlashCommand(command);
        return;
      }
      sendMessage();
      return;
    }

    if (!showPicker) {
      return;
    }

    // Wrap-around keyboard navigation for slash command list.
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setPickerIndex((prev) => (prev + 1) % slashMatches.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setPickerIndex((prev) => (prev - 1 + slashMatches.length) % slashMatches.length);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">Chat</div>

      {/* Scrollable message list — each row is a ChatMessage bubble. */}
      <div className="chat-messages">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            questionStates={questionStates}
            onQuestionAnswerChange={updateQuestionAnswer}
            onQuestionAccept={acceptQuestion}
          />
        ))}
      </div>

      <div className="chat-input-area">
        {showPicker && (
          <SlashCommandPicker
            input={input}
            selectedIndex={pickerIndex}
            onSelect={selectSlashCommand}
          />
        )}
        <div className="chat-input-row">
          <input
            className="chat-input"
            type="text"
            value={input}
            placeholder="Describe a part or ask a question…"
            disabled={sending}
            onChange={(e) => {
              setInput(e.target.value);
              setPickerIndex(0); // reset highlight when filter text changes
            }}
            onKeyDown={handleInputKeyDown}
          />
          <button className="chat-send" type="button" disabled={sending} onClick={sendMessage}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
