/**
 * ============================================================================
 * FILE: bridge.test.ts — Tests for IPC bridge envelope unwrapping
 * ============================================================================
 *
 * These tests run in Vitest with a fake window.copilotcad object. They verify
 * that bridge.ts correctly turns RpcEnvelope successes into values and failures
 * into Errors — and that executeIntent special-cases execution payloads in errors.
 * ============================================================================
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import { compileIntent, executeIntent, getPartMesh, listWorkspaceTree } from "./bridge";
import type { CopilotCADApi } from "./types";

/** Helper: attach a partial mock API to global window for one test file. */
function installApi(overrides: Partial<CopilotCADApi>): void {
  (window as unknown as { copilotcad: Partial<CopilotCADApi> }).copilotcad = overrides;
}

describe("ipc bridge envelope handling", () => {
  afterEach(() => {
    delete (window as unknown as { copilotcad?: unknown }).copilotcad;
    vi.restoreAllMocks();
  });

  it("returns the value from a successful envelope", async () => {
    installApi({
      compileIntent: vi.fn().mockResolvedValue({
        ok: true,
        value: { type: "part_create", prompt: "p", summary: "s", target: {} },
      }),
    });

    const result = await compileIntent("make a plate");
    expect(result.type).toBe("part_create");
  });

  it("throws an Error carrying code and data from an error envelope", async () => {
    installApi({
      compileIntent: vi.fn().mockResolvedValue({
        ok: false,
        error: { message: "boom", code: -32603, data: { error_type: "validation" } },
      }),
    });

    await expect(compileIntent("bad")).rejects.toMatchObject({
      message: "boom",
      code: -32603,
      data: { error_type: "validation" },
    });
  });

  it("recovers the execution payload when execute fails with payload in error data", async () => {
    installApi({
      getWorkspacePath: vi.fn().mockResolvedValue("/ws"),
      executeIntent: vi.fn().mockResolvedValue({
        ok: false,
        error: {
          message: "Execution failed",
          data: { success: false, step_ids: ["s1"], error: "kernel", problems: [] },
        },
      }),
    });

    const result = await executeIntent({
      type: "part_create",
      prompt: "p",
      summary: "s",
      target: {},
    });
    expect(result.success).toBe(false);
    expect(result.step_ids).toEqual(["s1"]);
  });

  it("passes workspace_path when executing intent", async () => {
    const executeIntentMock = vi.fn().mockResolvedValue({
      ok: true,
      value: { success: true, step_ids: ["s1"], final_step_id: "s1", problems: [] },
    });
    installApi({
      getWorkspacePath: vi.fn().mockResolvedValue("/ws"),
      executeIntent: executeIntentMock,
    });

    await executeIntent({
      type: "part_create",
      prompt: "p",
      summary: "s",
      target: { part_id: "mounting_plate" },
    });

    expect(executeIntentMock).toHaveBeenCalledWith(
      expect.objectContaining({ target: { part_id: "mounting_plate" } }),
      "/ws",
    );
  });

  it("unwraps a part mesh envelope", async () => {
    installApi({
      getPartMesh: vi.fn().mockResolvedValue({
        ok: true,
        value: { vertices: [0], normals: [0], indices: [0] },
      }),
    });

    const mesh = await getPartMesh("/ws", "mounting_plate");
    expect(mesh.vertices).toEqual([0]);
  });

  it("unwraps a workspace tree envelope", async () => {
    installApi({
      listWorkspaceTree: vi.fn().mockResolvedValue({
        ok: true,
        value: [{ name: "parts", path: "parts", type: "dir" }],
      }),
    });

    const tree = await listWorkspaceTree("/ws");
    expect(tree[0].name).toBe("parts");
  });
});
