/**
 * ============================================================================
 * FILE: AssumptionTag.test.tsx — Tests for assumption confirm/reject/edit (F-023)
 * ============================================================================
 *
 * Uses @testing-library/react to render the component in jsdom and simulate
 * button clicks. The IPC bridge is mocked so no Electron window is required.
 * ============================================================================
 */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import AssumptionTag from "./AssumptionTag";
import * as bridge from "../ipc/bridge";

vi.mock("../ipc/bridge", () => ({
  updateAssumption: vi.fn(),
}));

/** Shared fixture: a proposed high-importance assumption. */
const PROPOSED_ASSUMPTION = {
  id: "a1",
  text: "Plate thickness is 6 mm.",
  importance: "high" as const,
  status: "proposed" as const,
};

describe("AssumptionTag (F-023)", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders Confirm, Reject, and Edit actions for proposed assumptions", () => {
    render(
      <AssumptionTag
        assumption={PROPOSED_ASSUMPTION}
        partId="mounting_plate"
        onUpdated={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reject/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
  });

  it("calls updateAssumption on confirm", async () => {
    vi.mocked(bridge.updateAssumption).mockResolvedValue({ ok: true, value: {} });
    const onUpdated = vi.fn();

    render(
      <AssumptionTag
        assumption={PROPOSED_ASSUMPTION}
        partId="mounting_plate"
        onUpdated={onUpdated}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /confirm/i }));

    expect(bridge.updateAssumption).toHaveBeenCalledWith(
      "mounting_plate",
      "a1",
      "confirmed",
      undefined,
    );
  });

  it("updates displayed status after confirm", async () => {
    vi.mocked(bridge.updateAssumption).mockResolvedValue({ ok: true, value: {} });
    const onUpdated = vi.fn();

    render(
      <AssumptionTag
        assumption={PROPOSED_ASSUMPTION}
        partId="mounting_plate"
        onUpdated={onUpdated}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /confirm/i }));
    expect(onUpdated).toHaveBeenCalled();
  });

  it("allows editing assumption text", () => {
    render(
      <AssumptionTag
        assumption={PROPOSED_ASSUMPTION}
        partId="mounting_plate"
        onUpdated={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "8 mm thickness." } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    expect(bridge.updateAssumption).toHaveBeenCalledWith(
      "mounting_plate",
      "a1",
      "proposed",
      "8 mm thickness.",
    );
  });
});
