import { useState } from "react";

import { compileIntent } from "../ipc/bridge";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  text: "What to do first? Ask about this CAD model or we can start creating one.",
};

function formatError(err: unknown): string {
  if (err instanceof Error) {
    const withData = err as Error & { data?: { message?: string; error_type?: string } };
    if (withData.data?.message) {
      return `${err.message}: ${withData.data.message}`;
    }
    return err.message;
  }
  return String(err);
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    try {
      const result = await compileIntent(text);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: result.summary || "Intent IR compiled successfully.",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const assistantMessage: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        role: "assistant",
        text: `Could not compile intent: ${formatError(err)}`,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">Chat</div>
      <div className="chat-messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat-message chat-message-${message.role}`}
          >
            <div className="chat-message-label">
              {message.role === "user" ? "You" : "CopilotCAD"}
            </div>
            <div>{message.text}</div>
          </div>
        ))}
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          value={input}
          placeholder="Describe a part or ask a question…"
          disabled={sending}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              sendMessage();
            }
          }}
        />
        <button className="chat-send" type="button" disabled={sending} onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  );
}
