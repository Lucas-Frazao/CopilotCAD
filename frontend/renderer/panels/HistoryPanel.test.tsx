/**
 * HistoryPanel.test.tsx — Unit tests for Actions/Features history tabs
 *
 * HistoryPanel is mostly presentational — parent passes filtered entries.
 * Tests verify tab UI, timestamps, chat deep-link button, and part scoping.
 *
 * Feature: F-017
 */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import HistoryPanel from "./HistoryPanel";

/** Sample action log row with chat message link. */
const ACTION_ENTRIES = [
  {
    id: "h1",
    timestamp: "2026-06-01T12:00:00Z",
    type: "execute",
    summary: "Added corner holes",
    step_ids: ["s3"],
    message_id: "msg-42",
  },
];

/** Sample modeling steps for Features tab. */
const FEATURE_ENTRIES = [
  { id: "s1", op: "sketch_rectangle", label: "Sketch rectangle" },
  { id: "s2", op: "extrude", label: "Extrude 6 mm" },
];

describe("HistoryPanel (F-017)", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows Actions and Features sub-tabs", () => {
    render(
      <HistoryPanel
        partId="mounting_plate"
        actions={ACTION_ENTRIES}
        features={FEATURE_ENTRIES}
      />,
    );

    expect(screen.getByRole("tab", { name: /actions/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /features/i })).toBeInTheDocument();
  });

  it("lists action entries with timestamp and summary", () => {
    render(
      <HistoryPanel
        partId="mounting_plate"
        actions={ACTION_ENTRIES}
        features={[]}
      />,
    );

    expect(screen.getByText(/Added corner holes/i)).toBeInTheDocument();
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("links action entry to chat message when message_id stored", () => {
    const onOpenChat = vi.fn();
    render(
      <HistoryPanel
        partId="mounting_plate"
        actions={ACTION_ENTRIES}
        features={[]}
        onOpenChatMessage={onOpenChat}
      />,
    );

    screen.getByRole("button", { name: /open in chat/i }).click();
    expect(onOpenChat).toHaveBeenCalledWith("msg-42");
  });

  it("Feature tab lists modeling steps in order", () => {
    render(
      <HistoryPanel
        partId="mounting_plate"
        actions={[]}
        features={FEATURE_ENTRIES}
        initialTab="features"
      />,
    );

    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent(/sketch/i);
    expect(items[1]).toHaveTextContent(/extrude/i);
  });

  it("filters history by active part only", () => {
    const { rerender } = render(
      <HistoryPanel partId="mounting_plate" actions={ACTION_ENTRIES} features={[]} />,
    );
    expect(screen.getByText(/Added corner holes/i)).toBeInTheDocument();

    // Parent passes empty actions when switching to a different part.
    rerender(<HistoryPanel partId="bracket" actions={[]} features={[]} />);
    expect(screen.queryByText(/Added corner holes/i)).not.toBeInTheDocument();
  });
});
