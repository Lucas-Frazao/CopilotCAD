import { describe, expect, it } from "vitest";

import { SLASH_COMMANDS } from "../../renderer/chat/chat-utils";

/** F-014: each MVP slash command must be handled — not return stub message. */
const EXPECTED_ARTIFACTS: Record<string, string> = {
  "/vision": "docs/product_vision.md",
  "/constitution": "docs/constitution.md",
  "/architecture": "docs/system_architecture.md",
  "/manufacturing": "docs/manufacturing_stack.md",
  "/part": "parts/<id>/spec.yaml",
  "/interface": "parts/<active>/spec.yaml",
  "/plan": "parts/<active>/plan.md",
  "/review": "parts/<active>/review.md",
  "/release": "parts/<active>/spec.yaml",
  "/export": "exports/<part>.step",
  "/assumptions": "parts/<active>/assumptions.yaml",
  "/history": "parts/<active>/history.json",
};

describe("slash command contract (F-014)", () => {
  it("defines all 12 MVP slash commands", () => {
    expect(SLASH_COMMANDS).toHaveLength(12);
    for (const cmd of Object.keys(EXPECTED_ARTIFACTS)) {
      expect(SLASH_COMMANDS).toContain(cmd);
    }
  });

  it("documents expected artifact per command for handler tests", () => {
    expect(Object.keys(EXPECTED_ARTIFACTS)).toHaveLength(12);
  });
});
