/**
 * slash-commands-f014.test.ts — Slash command registry contract
 *
 * Documents the 12 MVP slash commands and which project artifact each command
 * should touch. Handler integration tests use EXPECTED_ARTIFACTS as a checklist.
 *
 * Feature: F-014
 */

import { describe, expect, it } from "vitest";

import { SLASH_COMMANDS } from "../../renderer/chat/chat-utils";

/**
 * Map each slash command to the file path pattern it should read or write.
 * Used by backend/frontend handler tests — not enforced at runtime here.
 */
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
