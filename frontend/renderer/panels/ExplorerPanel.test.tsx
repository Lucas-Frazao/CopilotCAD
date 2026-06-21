import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ExplorerPanel from "./ExplorerPanel";
import type { WorkspaceTreeNode } from "../ipc/types";
import * as bridge from "../ipc/bridge";

vi.mock("../ipc/bridge", () => ({
  listWorkspaceTree: vi.fn(),
  readWorkspaceFile: vi.fn(),
}));

const SAMPLE_TREE: WorkspaceTreeNode[] = [
  {
    name: "parts",
    path: "parts",
    type: "dir",
    children: [
      {
        name: "mounting_plate",
        path: "parts/mounting_plate",
        type: "dir",
        children: [
          {
            name: "spec.yaml",
            path: "parts/mounting_plate/spec.yaml",
            type: "file",
          },
        ],
      },
    ],
  },
];

describe("ExplorerPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(bridge.listWorkspaceTree).mockResolvedValue(SAMPLE_TREE);
    vi.mocked(bridge.readWorkspaceFile).mockResolvedValue({
      contents: "part_id: mounting_plate\n",
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("loads workspace tree on mount", async () => {
    render(<ExplorerPanel workspacePath="/tmp/example_project" />);

    await waitFor(() => {
      expect(bridge.listWorkspaceTree).toHaveBeenCalledWith(
        "/tmp/example_project",
      );
    });

    expect(await screen.findByText("parts")).toBeInTheDocument();
  });

  it("shows file preview when a file is selected", async () => {
    render(<ExplorerPanel workspacePath="/tmp/example_project" />);

    const expandParts = await screen.findByRole("button", {
      name: /expand parts/i,
    });
    fireEvent.click(expandParts);

    const expandPart = await screen.findByRole("button", {
      name: /expand mounting_plate/i,
    });
    fireEvent.click(expandPart);

    fireEvent.click(screen.getByRole("button", { name: /spec.yaml/i }));

    await waitFor(() => {
      expect(bridge.readWorkspaceFile).toHaveBeenCalledWith(
        "/tmp/example_project",
        "parts/mounting_plate/spec.yaml",
      );
    });

    expect(
      await screen.findByText("part_id: mounting_plate"),
    ).toBeInTheDocument();
  });

  it("refetches tree when refreshToken changes", async () => {
    const { rerender } = render(
      <ExplorerPanel workspacePath="/tmp/example_project" refreshToken={0} />,
    );

    await waitFor(() => {
      expect(bridge.listWorkspaceTree).toHaveBeenCalledTimes(1);
    });

    rerender(
      <ExplorerPanel workspacePath="/tmp/example_project" refreshToken={1} />,
    );

    await waitFor(() => {
      expect(bridge.listWorkspaceTree).toHaveBeenCalledTimes(2);
    });
  });
});
