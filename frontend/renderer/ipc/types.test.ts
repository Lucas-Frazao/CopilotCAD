import { describe, expect, it } from "vitest";

import type {
  ExecuteIntentResult,
  IntentIRPayload,
  WorkspaceFileContents,
  WorkspaceTreeNode,
} from "./types";

describe("ipc types", () => {
  it("IntentIRPayload includes summary and target", () => {
    const payload: IntentIRPayload = {
      type: "part_create",
      prompt: "Create a plate",
      summary: "Create mounting plate",
      target: { part_id: "mounting_plate" },
    };

    expect(payload.summary).toBe("Create mounting plate");
    expect(payload.target.part_id).toBe("mounting_plate");
  });

  it("ExecuteIntentResult includes problems array", () => {
    const result: ExecuteIntentResult = {
      success: true,
      step_ids: ["step_1"],
      final_step_id: "step_1",
      problems: [
        {
          id: "traceability_gap:mounting_plate",
          type: "traceability_gap",
          severity: "warning",
          message: "Missing traceability",
        },
      ],
    };

    expect(result.problems[0].type).toBe("traceability_gap");
    expect(result.step_ids).toEqual(["step_1"]);
  });

  it("WorkspaceTreeNode supports nested directories", () => {
    const node: WorkspaceTreeNode = {
      name: "parts",
      path: "parts",
      type: "dir",
      children: [
        {
          name: "spec.yaml",
          path: "parts/mounting_plate/spec.yaml",
          type: "file",
        },
      ],
    };

    expect(node.children?.[0].type).toBe("file");
  });

  it("WorkspaceFileContents wraps text payload", () => {
    const payload: WorkspaceFileContents = { contents: "hello" };
    expect(payload.contents).toBe("hello");
  });
});
