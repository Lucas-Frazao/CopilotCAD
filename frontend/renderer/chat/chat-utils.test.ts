import { describe, expect, it } from "vitest";

import { buildDiffSummaryText, filterSlashCommands, isSlashOnlyMessage, isConversationalMessage, formatCompileError } from "../../renderer/chat/chat-utils";
import type { ExecuteIntentResult } from "../../renderer/ipc/types";

describe("chat-utils", () => {
  it("buildDiffSummaryText describes successful execution", () => {
    const execution: ExecuteIntentResult = {
      success: true,
      step_ids: ["sketch_1", "extrude_1"],
      final_step_id: "extrude_1",
      problems: [],
    };

    expect(buildDiffSummaryText(execution)).toBe(
      "Executed 2 step(s): sketch_1, extrude_1. Final step: extrude_1.",
    );
  });

  it("buildDiffSummaryText describes failed execution", () => {
    const execution: ExecuteIntentResult = {
      success: false,
      step_ids: ["sketch_1"],
      error: "Kernel error",
      problems: [],
    };

    expect(buildDiffSummaryText(execution)).toBe(
      "Execution failed: Kernel error. Steps attempted: sketch_1.",
    );
  });

  it("filterSlashCommands matches typed prefix", () => {
    expect(filterSlashCommands("/par")).toEqual(["/part"]);
    expect(filterSlashCommands("/")).toHaveLength(12);
  });

  it("isSlashOnlyMessage detects MVP slash commands", () => {
    expect(isSlashOnlyMessage("/export")).toBe(true);
    expect(isSlashOnlyMessage("/export step")).toBe(false);
    expect(isSlashOnlyMessage("hello")).toBe(false);
  });

  it("isConversationalMessage detects greetings", () => {
    expect(isConversationalMessage("Hello!")).toBe(true);
    expect(isConversationalMessage("thanks")).toBe(true);
    expect(isConversationalMessage("Create a plate")).toBe(false);
  });

  it("formatCompileError returns friendly validation message", () => {
    const err = new Error("RPC failed") as Error & {
      data?: { error_type: string; message: string };
    };
    err.data = { error_type: "validation", message: "Intent IR validation failed" };
    expect(formatCompileError(err)).toContain("modeling plan");
  });
});
