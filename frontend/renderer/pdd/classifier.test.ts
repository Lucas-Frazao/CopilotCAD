/**
 * ============================================================================
 * FILE: classifier.test.ts — Tests for client-side PDD complexity heuristics
 * ============================================================================
 *
 * Ensures simple dimensional plate prompts stay "simple" while assembly-style
 * language triggers suggest_pdd, and that quick-reply actions are offered.
 * Feature F-013.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";

import { classifyRequestComplexity, buildPddSuggestionActions } from "../../renderer/pdd/classifier";

describe("PDD suggestion engine (F-013)", () => {
  it("does not suggest PDD for simple plate prompts", () => {
    const result = classifyRequestComplexity(
      "Create a 100×50×6 mm mounting plate with 6 mm corner holes.",
    );
    expect(result.classification).toBe("simple");
  });

  it("suggests PDD for complex multi-part prompts", () => {
    const result = classifyRequestComplexity(
      "Build a drone frame with motor mounts and battery bay.",
    );
    expect(result.classification).toBe("suggest_pdd");
    expect(result.reason.length).toBeGreaterThan(0);
  });

  it("offers at least two quick-reply actions", () => {
    const actions = buildPddSuggestionActions();
    expect(actions.length).toBeGreaterThanOrEqual(2);
    const labels = actions.map((a) => a.label.toLowerCase());
    expect(labels.some((l) => l.includes("pdd") || l.includes("/vision"))).toBe(true);
    expect(labels.some((l) => l.includes("proceed") || l.includes("continue"))).toBe(true);
  });
});
