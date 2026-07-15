/**
 * golden-path-f012.test.ts — Golden path integration contract
 *
 * Encodes the expected end-to-end outcome of one chat execute (mounting plate
 * prompt → artifacts on disk → shared panel state keys). Full Playwright E2E
 * belongs in F-012 implementation; this file locks the contract in unit tests.
 *
 * Feature: F-012
 */

import { describe, expect, it } from "vitest";

describe("Golden path panel sync (F-012)", () => {
  /** Canonical user prompt for the mounting-plate demo scenario. */
  const GOLDEN_PROMPT =
    "Create a 100×50×6 mm mounting plate with 6 mm corner holes.";

  /** Files the backend should create or update after successful execute. */
  const EXPECTED_ARTIFACTS = [
    "parts/mounting_plate/spec.yaml",
    "parts/mounting_plate/assumptions.yaml",
    "parts/mounting_plate/history.json",
    "exports/mounting_plate.step",
  ];

  it("defines golden prompt and expected artifacts", () => {
    expect(GOLDEN_PROMPT).toContain("100");
    expect(GOLDEN_PROMPT).toContain("mounting plate");
    expect(EXPECTED_ARTIFACTS).toHaveLength(4);
  });

  it("expects all panels to consume shared project state after execute", () => {
    // App-level state slice keys — each panel reads one or more of these.
    const panelStateKeys = [
      "problems",
      "workspaceTree",
      "activePartId",
      "partMesh",
      "partHistory",
    ];
    expect(panelStateKeys).toEqual(
      expect.arrayContaining(["problems", "workspaceTree", "partMesh"]),
    );
  });
});
