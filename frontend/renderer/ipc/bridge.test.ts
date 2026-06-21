import { afterEach, describe, expect, it, vi } from "vitest";

import { compileIntent, executeIntent, listWorkspaceTree } from "./bridge";
import type { CopilotCADApi } from "./types";

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
