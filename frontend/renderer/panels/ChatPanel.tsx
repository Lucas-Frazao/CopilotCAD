import { useState, type KeyboardEvent } from "react";

import type { ChatMessageData, QuestionLocalState } from "../chat/chat-types";
import { filterSlashCommands, isSlashOnlyMessage, isConversationalMessage, CONVERSATIONAL_REPLY, formatCompileError } from "../chat/chat-utils";
import ChatMessage from "../components/ChatMessage";
import SlashCommandPicker from "../components/SlashCommandPicker";
import { compileIntent, executeIntent } from "../ipc/bridge";

// Monotonic counter for React keys / message ids. Date.now() collided when two
// messages were created in the same millisecond (e.g. a user turn plus its
// immediate local reply), producing duplicate keys.
let messageSeq = 0;
function nextMessageId(prefix: string): string {
  messageSeq += 1;
  return `${prefix}-${messageSeq}`;
}

const WELCOME: ChatMessageData = {
  id: "welcome",
  role: "assistant",
  kind: "text",
  text: "What to do first? Ask about this CAD model or we can start creating one.",
};

export default function ChatPanel({
  onWorkspaceChanged,
}: {
  onWorkspaceChanged?: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessageData[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pickerIndex, setPickerIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<Record<string, QuestionLocalState>>({});

  const slashMatches = filterSlashCommands(input);
  const showPicker = input.startsWith("/") && slashMatches.length > 0;

  const selectSlashCommand = (command: string) => {
    setInput(`${command} `);
    setPickerIndex(0);
  };

  const updateQuestionAnswer = (questionId: string, answer: string) => {
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        status: prev[questionId]?.status ?? "open",
        answer,
      },
    }));
  };

  const acceptQuestion = (questionId: string) => {
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        status: "answered",
        answer: prev[questionId]?.answer ?? "",
      },
    }));
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) {
      return;
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

    try {
      const intent = await compileIntent(text);
      const execution = await executeIntent(intent);
      if (execution.success) {
        onWorkspaceChanged?.();
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
              setPickerIndex(0);
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
