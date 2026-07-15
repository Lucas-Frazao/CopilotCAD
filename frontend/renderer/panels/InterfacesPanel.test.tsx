/**
 * InterfacesPanel.test.tsx — Unit tests for assembly interface list
 *
 * Verifies row content, part selection callback, conflict highlight styling,
 * and empty state. No IPC — pure props-in, DOM-out component.
 *
 * Feature: F-016
 */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import InterfacesPanel from "./InterfacesPanel";

/** Two interfaces: one open, one linked to mounting_plate. */
const SAMPLE_INTERFACES = [
  {
    part_id: "mounting_plate",
    interface_id: "mount_a",
    name: "Mount face",
    type: "mechanical",
    status: "open" as const,
    connected_part_id: null,
  },
  {
    part_id: "bracket",
    interface_id: "mount_b",
    name: "Bracket mount",
    type: "mechanical",
    status: "linked" as const,
    connected_part_id: "mounting_plate",
  },
];

describe("InterfacesPanel (F-016)", () => {
  afterEach(() => {
    cleanup();
  });

  it("lists interfaces with part id, name, type, and status", () => {
    render(<InterfacesPanel interfaces={SAMPLE_INTERFACES} />);

    expect(screen.getByText(/mount_a/i)).toBeInTheDocument();
    expect(screen.getByText(/mechanical/i)).toBeInTheDocument();
    expect(screen.getByText(/open/i)).toBeInTheDocument();
    expect(screen.getByText(/linked/i)).toBeInTheDocument();
  });

  it("clicking a row selects the part in explorer context", () => {
    const onSelect = vi.fn();
    render(
      <InterfacesPanel interfaces={SAMPLE_INTERFACES} onSelectPart={onSelect} />,
    );

    fireEvent.click(screen.getByText(/mount_a/i));
    expect(onSelect).toHaveBeenCalledWith("mounting_plate");
  });

  it("highlights row when interface_conflict problem references interface", () => {
    render(
      <InterfacesPanel
        interfaces={SAMPLE_INTERFACES}
        highlightedInterfaceId="mount_a"
      />,
    );
    const row = screen.getByTestId("interface-row-mount_a");
    expect(row).toHaveClass("highlighted");
  });

  it("shows empty state when no interfaces defined", () => {
    render(<InterfacesPanel interfaces={[]} />);
    expect(screen.getByText(/no interfaces/i)).toBeInTheDocument();
  });
});
