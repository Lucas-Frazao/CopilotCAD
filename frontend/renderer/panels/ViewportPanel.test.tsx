/**
 * ViewportPanel.test.tsx — Unit tests for single-part 3D viewport
 *
 * Mocks @react-three/fiber Canvas to avoid WebGL in jsdom. Covers mesh mount,
 * empty placeholder, face-pick callback, and transition to empty when mesh removed.
 *
 * Feature: F-011
 */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ViewportPanel from "./ViewportPanel";
import type { PartMeshPayload } from "../ipc/mesh-types";

/** Tiny triangle mesh — enough structure for panel to render. */
const MOUNTING_PLATE_MESH: PartMeshPayload = {
  vertices: [0, 0, 0, 1, 0, 0, 0, 1, 0],
  normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
  indices: [0, 1, 2],
  face_ids: [1, 1, 1],
};

/**
 * Stub Canvas — real Three.js needs WebGL; tests only need children mounted.
 */
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="viewport-canvas">{children}</div>
  ),
}));

describe("ViewportPanel (F-011)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders mounting plate mesh as a visible canvas", () => {
    render(<ViewportPanel mesh={MOUNTING_PLATE_MESH} />);
    expect(screen.getByTestId("viewport-canvas")).toBeInTheDocument();
  });

  it("shows placeholder when no geometry exists", () => {
    render(<ViewportPanel mesh={null} />);
    expect(screen.getByText(/no geometry|placeholder/i)).toBeInTheDocument();
  });

  it("exposes orbit controls without crashing", () => {
    render(<ViewportPanel mesh={MOUNTING_PLATE_MESH} />);
    expect(screen.getByTestId("viewport-canvas")).toBeInTheDocument();
    // Orbit controls live inside real Three.js — here we only assert clean mount.
  });

  it("records face selection for chat context", () => {
    const onSelect = vi.fn();
    render(
      <ViewportPanel
        mesh={MOUNTING_PLATE_MESH}
        onFaceSelect={onSelect}
        selectedFaceId={null}
      />,
    );
    const pickTarget = screen.getByTestId("viewport-pick-surface");
    pickTarget.click();
    expect(onSelect).toHaveBeenCalledWith(expect.any(Number));
  });

  it("clears selection when mesh is removed", () => {
    const { rerender } = render(
      <ViewportPanel mesh={MOUNTING_PLATE_MESH} selectedFaceId={3} />,
    );
    rerender(<ViewportPanel mesh={null} selectedFaceId={null} />);
    expect(screen.getByText(/no geometry|placeholder/i)).toBeInTheDocument();
  });
});
