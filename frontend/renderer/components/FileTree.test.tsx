/**
 * ============================================================================
 * FILE: FileTree.test.tsx — Unit tests for workspace file tree UI
 * ============================================================================
 *
 * Verifies rendering, expand toggles, nested visibility when expandedPaths
 * contains parent paths, and file selection callbacks.
 * ============================================================================
 */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FileTree from "./FileTree";
import type { WorkspaceTreeNode } from "../ipc/types";

/** Nested sample tree matching real workspace layout (parts/.../spec.yaml). */
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

describe("FileTree", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders top-level folder nodes", () => {
    render(
      <FileTree
        nodes={SAMPLE_TREE}
        selectedPath={null}
        expandedPaths={new Set()}
        onSelect={vi.fn()}
        onToggleExpand={vi.fn()}
      />,
    );

    expect(screen.getByText("parts")).toBeInTheDocument();
  });

  it("expands folders when toggle is clicked", () => {
    const onToggleExpand = vi.fn();

    render(
      <FileTree
        nodes={SAMPLE_TREE}
        selectedPath={null}
        expandedPaths={new Set()}
        onSelect={vi.fn()}
        onToggleExpand={onToggleExpand}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /expand parts/i }));
    expect(onToggleExpand).toHaveBeenCalledWith("parts");
  });

  it("shows nested files when parent path is expanded", () => {
    render(
      <FileTree
        nodes={SAMPLE_TREE}
        selectedPath={null}
        expandedPaths={new Set(["parts", "parts/mounting_plate"])}
        onSelect={vi.fn()}
        onToggleExpand={vi.fn()}
      />,
    );

    expect(screen.getByText("spec.yaml")).toBeInTheDocument();
  });

  it("calls onSelect when a file is clicked", () => {
    const onSelect = vi.fn();

    render(
      <FileTree
        nodes={SAMPLE_TREE}
        selectedPath={null}
        expandedPaths={new Set(["parts", "parts/mounting_plate"])}
        onSelect={onSelect}
        onToggleExpand={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /spec.yaml/i }));
    expect(onSelect).toHaveBeenCalledWith(
      "parts/mounting_plate/spec.yaml",
      "file",
    );
  });
});
