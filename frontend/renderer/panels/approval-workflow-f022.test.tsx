/**
 * approval-workflow-f022.test.tsx — Approval gate UI in chat messages
 *
 * Tests ChatMessage (not ChatPanel) for F-022 risk approval flow: destructive
 * intents show Approve/Reject; callbacks receive pendingId without executing.
 *
 * Feature: F-022
 */

import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ChatMessage from "../components/ChatMessage";
import type { ChatMessageData } from "../chat/chat-types";

describe("Approval workflow chat UI (F-022)", () => {
  afterEach(() => {
    cleanup();
  });

  /** Representative approval_required bubble — delete part intent. */
  const approvalMessage: ChatMessageData = {
    id: "approval-1",
    role: "assistant",
    kind: "approval_required",
    text: "This will remove parts/mounting_plate and related files.",
    intent: {
      type: "part_edit",
      prompt: "delete",
      summary: "Delete mounting plate",
      target: { part_id: "mounting_plate" },
    },
  };

  it("renders approval_required message with Approve and Reject buttons", () => {
    render(
      <ChatMessage
        message={approvalMessage}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    );

    expect(screen.getByText(/remove parts\/mounting_plate/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reject/i })).toBeInTheDocument();
  });

  it("calls onApprove with pending id when approved", () => {
    const onApprove = vi.fn();
    render(
      <ChatMessage
        message={{ ...approvalMessage, pendingId: "pending-42" }}
        onApprove={onApprove}
        onReject={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /approve/i }));
    expect(onApprove).toHaveBeenCalledWith("pending-42");
  });

  it("calls onReject without executing when rejected", () => {
    const onReject = vi.fn();
    render(
      <ChatMessage
        message={{ ...approvalMessage, pendingId: "pending-42" }}
        onApprove={vi.fn()}
        onReject={onReject}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /reject/i }));
    expect(onReject).toHaveBeenCalledWith("pending-42");
  });
});
