import { describe, expect, it } from "vitest";

import type { IntentIRPayload } from "./types";

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
});
