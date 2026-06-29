/**
 * ============================================================================
 * FILE: formatUserError.test.ts — Tests for user-facing error strings (F-026)
 * ============================================================================
 *
 * Ensures technical RPC/IPC errors become short, helpful chat messages and
 * never leak raw "Error invoking remote method" blobs to the user.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";

import { formatUserError } from "../../renderer/errors/formatUserError";

describe("formatUserError (F-026)", () => {
  it("formats compile validation errors with actionable guidance", () => {
    const err = {
      message: "RPC failed",
      data: { error_type: "validation", message: "Intent IR validation failed" },
    };
    const text = formatUserError(err);
    expect(text).not.toContain("Traceback");
    expect(text.toLowerCase()).toMatch(/dimensions|modeling plan|rephras/);
  });

  it("formats export-without-geometry errors", () => {
    const text = formatUserError({
      message: "export failed",
      data: { error_type: "export", message: "No geometry" },
    });
    expect(text.toLowerCase()).toMatch(/model|geometry|first/);
  });

  it("formats slash command usage errors", () => {
    const text = formatUserError({
      message: "bad args",
      data: { error_type: "slash", message: "Usage: /part <name>" },
    });
    expect(text).toContain("/part");
  });

  it("formats missing API key configuration errors", () => {
    const text = formatUserError({
      message: "config",
      data: { error_type: "configuration" },
    });
    expect(text).toContain("ANTHROPIC_API_KEY");
  });

  it("never returns raw JSON-RPC blobs", () => {
    const text = formatUserError({
      message: 'Error invoking remote method "compile_intent"',
    });
    expect(text).not.toContain("Error invoking remote method");
    expect(text.length).toBeGreaterThan(10);
  });

  it("includes bullet suggestions when provided", () => {
    const text = formatUserError({
      data: {
        error_type: "execution",
        suggested_next_steps: ["Confirm assumption a2", "Add thickness to prompt"],
      },
    });
    expect(text).toContain("Confirm assumption a2");
    expect(text).toContain("Add thickness");
  });
});
