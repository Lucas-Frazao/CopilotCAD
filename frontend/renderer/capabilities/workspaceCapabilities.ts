/**
 * ============================================================================
 * FILE: workspaceCapabilities.ts — Edition limits and soft-cap checks (F-027)
 * ============================================================================
 *
 * CopilotCAD can ship different "editions" (community vs pro vs team) with
 * different limits (max parts, export formats, etc.). The backend sends real
 * capability flags; this module holds TypeScript types and frontend helpers
 * for defaults and soft-limit warning messages.
 * ============================================================================
 */

/**
 * WorkspaceCapabilities — flags and numeric limits for the open workspace.
 */
export interface WorkspaceCapabilities {
  // Which product tier this workspace uses.
  edition: "community" | "pro" | "team";
  // Maximum parts allowed in the project tree.
  max_parts: number;
  // Maximum parts inside one assembly.
  max_assembly_parts: number;
  // Whether assembly features are enabled at all.
  assembly_enabled: boolean;
  // Whether STEP file export is allowed.
  export_step: boolean;
  // Whether IGES export is allowed.
  export_iges: boolean;
}

/**
 * COMMUNITY_DEFAULTS — baseline limits when backend does not override.
 * Used in tests and offline UI until workspace manifest loads.
 */
const COMMUNITY_DEFAULTS: WorkspaceCapabilities = {
  edition: "community",
  max_parts: 10,
  max_assembly_parts: 5,
  assembly_enabled: true,
  export_step: true,
  export_iges: true,
};

/**
 * defaultCapabilities — merge optional partial overrides onto community defaults.
 *
 * The spread operator {...A, ...B} copies fields; later keys in B win.
 */
export function defaultCapabilities(
  partial?: Partial<WorkspaceCapabilities>,
): WorkspaceCapabilities {
  return { ...COMMUNITY_DEFAULTS, ...partial };
}

/**
 * checkSoftLimit — return a warning string if current count exceeds a numeric cap.
 *
 * @param caps - Active capability object.
 * @param limitKey - Which numeric field on caps to compare (e.g. max_parts).
 * @param current - How many items exist now.
 * @returns Warning message or null if under limit / not a number field.
 */
export function checkSoftLimit(
  caps: WorkspaceCapabilities,
  limitKey: keyof WorkspaceCapabilities,
  current: number,
): string | null {
  const limit = caps[limitKey];
  // Skip non-numeric keys like edition or boolean flags.
  if (typeof limit !== "number") {
    return null;
  }
  if (current > limit) {
    return `Community limit reached for ${String(limitKey)} (${current}/${limit}).`;
  }
  return null;
}
