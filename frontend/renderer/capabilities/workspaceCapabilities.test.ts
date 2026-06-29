/**
 * ============================================================================
 * FILE: workspaceCapabilities.test.ts — Tests for edition limits (F-027)
 * ============================================================================
 *
 * Verifies default community caps and checkSoftLimit warning messages without
 * loading a real workspace or backend manifest.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";

import { checkSoftLimit, defaultCapabilities } from "../../renderer/capabilities/workspaceCapabilities";

describe("workspace capabilities (F-027)", () => {
  it("loads community defaults with documented limits", () => {
    const caps = defaultCapabilities();
    expect(caps.edition).toBe("community");
    expect(caps.max_assembly_parts).toBeLessThanOrEqual(5);
    expect(caps.export_step).toBe(true);
    expect(caps.export_iges).toBe(true);
  });

  it("returns warning message when assembly part limit exceeded", () => {
    const caps = defaultCapabilities();
    const warning = checkSoftLimit(caps, "max_assembly_parts", 6);
    expect(warning).not.toBeNull();
    expect(warning!.toLowerCase()).toMatch(/community|limit/);
  });

  it("returns null when within soft limit", () => {
    const caps = defaultCapabilities();
    expect(checkSoftLimit(caps, "max_assembly_parts", 3)).toBeNull();
  });

  it("backward compatible when optional fields missing", () => {
    const caps = defaultCapabilities({ edition: "community" });
    expect(caps.max_parts).toBeGreaterThan(0);
  });
});
