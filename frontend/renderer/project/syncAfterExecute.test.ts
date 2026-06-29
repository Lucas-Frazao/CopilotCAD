/**
 * ============================================================================
 * FILE: syncAfterExecute.test.ts — Unit tests for post-execute UI sync
 * ============================================================================
 *
 * Vitest tests verify syncProjectStateAfterExecute updates Zustand store and
 * calls IPC only when geometry was actually produced. Mocks replace real
 * Electron bridge so tests run in Node without a desktop window.
 * ============================================================================
 */

// Vitest test primitives: describe groups tests; it runs one case; expect asserts.
import { afterEach, describe, expect, it, vi } from "vitest";

// Function under test.
import { syncProjectStateAfterExecute } from "./syncAfterExecute";
// Global store we assert against after sync.
import { useAppStore } from "../store/appStore";

// vi.mock replaces ../ipc/bridge with fake implementations for this file only.
vi.mock("../ipc/bridge", () => ({
  getWorkspacePath: vi.fn().mockResolvedValue("/ws"),
  getPartMesh: vi.fn().mockResolvedValue({
    vertices: [0, 0, 0],
    normals: [0, 0, 1],
    indices: [0, 1, 2],
  }),
}));

describe("syncProjectStateAfterExecute", () => {
  // Reset store and mock call history after each test so cases stay isolated.
  afterEach(() => {
    useAppStore.setState({
      activePartId: null,
      problems: [],
      partMesh: null,
    });
    vi.clearAllMocks();
  });

  it("loads mesh and updates shared state after successful execute", async () => {
    await syncProjectStateAfterExecute(
      {
        type: "part_create",
        prompt: "p",
        summary: "s",
        target: { part_id: "mounting_plate" },
      },
      {
        success: true,
        step_ids: ["s1", "s2", "s3"],
        final_step_id: "s3",
        problems: [
          {
            id: "assumption:1",
            type: "unresolved_assumption",
            severity: "warning",
            message: "Assumption pending",
          },
        ],
      },
    );

    const state = useAppStore.getState();
    expect(state.activePartId).toBe("mounting_plate");
    expect(state.problems).toHaveLength(1);
    expect(state.partMesh?.vertices).toEqual([0, 0, 0]);
  });

  it("skips mesh fetch when execute did not produce geometry", async () => {
    const { getPartMesh } = await import("../ipc/bridge");

    await syncProjectStateAfterExecute(
      {
        type: "part_create",
        prompt: "p",
        summary: "s",
        target: { part_id: "mounting_plate" },
      },
      {
        success: true,
        step_ids: [],
        final_step_id: null,
        problems: [],
      },
    );

    expect(getPartMesh).not.toHaveBeenCalled();
    expect(useAppStore.getState().partMesh).toBeNull();
  });
});
