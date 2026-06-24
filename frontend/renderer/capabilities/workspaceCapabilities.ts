/** Workspace edition and capability helpers (F-027). */

export interface WorkspaceCapabilities {
  edition: "community" | "pro" | "team";
  max_parts: number;
  max_assembly_parts: number;
  assembly_enabled: boolean;
  export_step: boolean;
  export_iges: boolean;
}

const COMMUNITY_DEFAULTS: WorkspaceCapabilities = {
  edition: "community",
  max_parts: 10,
  max_assembly_parts: 5,
  assembly_enabled: true,
  export_step: true,
  export_iges: true,
};

export function defaultCapabilities(
  partial?: Partial<WorkspaceCapabilities>,
): WorkspaceCapabilities {
  return { ...COMMUNITY_DEFAULTS, ...partial };
}

export function checkSoftLimit(
  caps: WorkspaceCapabilities,
  limitKey: keyof WorkspaceCapabilities,
  current: number,
): string | null {
  const limit = caps[limitKey];
  if (typeof limit !== "number") {
    return null;
  }
  if (current > limit) {
    return `Community limit reached for ${String(limitKey)} (${current}/${limit}).`;
  }
  return null;
}
