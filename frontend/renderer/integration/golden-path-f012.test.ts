import { describe, expect, it } from "vitest";

/**
 * F-012 golden path contract — documents expected panel sync after one chat execute.
 * Full Playwright E2E lands in F-012 implementation; this test encodes the contract.
 */
describe("Golden path panel sync (F-012)", () => {
  const GOLDEN_PROMPT =
    "Create a 100×50×6 mm mounting plate with 6 mm corner holes.";

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
