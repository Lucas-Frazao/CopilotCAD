import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ViewportPanel from "./ViewportPanel";
import type { AssemblyMeshPayload } from "../ipc/mesh-types";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="assembly-viewport-canvas">{children}</div>
  ),
}));

const ASSEMBLY_MESH: AssemblyMeshPayload = {
  meshes: [
    {
      instance_id: "inst_plate",
      part_id: "mounting_plate",
      vertices: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
      indices: [0, 1, 2],
      transform: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    },
    {
      instance_id: "inst_bracket",
      part_id: "bracket",
      vertices: [0, 0, 0, 1, 0, 0, 0, 1, 0],
      normals: [0, 0, 1, 0, 0, 1, 0, 0, 1],
      indices: [0, 1, 2],
      transform: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 10, 0, 0, 1],
    },
  ],
};

describe("Assembly viewport (F-020)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders multiple instance meshes in one scene", () => {
    render(<ViewportPanel assemblyMesh={ASSEMBLY_MESH} mode="assembly" />);
    expect(screen.getByTestId("assembly-viewport-canvas")).toBeInTheDocument();
    expect(screen.getByTestId("mesh-inst_plate")).toBeInTheDocument();
    expect(screen.getByTestId("mesh-inst_bracket")).toBeInTheDocument();
  });

  it("shows assembly tree listing instances", () => {
    render(<ViewportPanel assemblyMesh={ASSEMBLY_MESH} mode="assembly" />);
    expect(screen.getByText(/mounting_plate/i)).toBeInTheDocument();
    expect(screen.getByText(/bracket/i)).toBeInTheDocument();
  });

  it("passes instance_id to selection handler on instance click", () => {
    const onSelectInstance = vi.fn();
    render(
      <ViewportPanel
        assemblyMesh={ASSEMBLY_MESH}
        mode="assembly"
        onSelectInstance={onSelectInstance}
      />,
    );

    screen.getByTestId("instance-inst_bracket").click();
    expect(onSelectInstance).toHaveBeenCalledWith(
      expect.objectContaining({ instance_id: "inst_bracket", part_id: "bracket" }),
    );
  });

  it("single-part mode still works when no assembly active", () => {
    render(<ViewportPanel mode="part" mesh={null} />);
    expect(screen.getByText(/no geometry|placeholder/i)).toBeInTheDocument();
  });
});
