import { create } from "zustand";

import { defaultCapabilities, type WorkspaceCapabilities } from "../capabilities/workspaceCapabilities";
import type { PartMeshPayload } from "../ipc/mesh-types";
import type { BackendStatus, ProblemPayload } from "../ipc/types";

/**
 * Global UI state that several panels need to react to: backend health and any
 * failure to resolve the workspace. Previously every panel kept this in local
 * state, so an IPC failure (e.g. backend down) had no shared place to surface.
 */
interface AppState {
  backendStatus: BackendStatus;
  workspaceError: string | null;
  problems: ProblemPayload[];
  activePartId: string | null;
  partMesh: PartMeshPayload | null;
  capabilities: WorkspaceCapabilities;
  setBackendStatus: (status: BackendStatus) => void;
  setWorkspaceError: (message: string | null) => void;
  setProblems: (problems: ProblemPayload[]) => void;
  setActivePartId: (partId: string | null) => void;
  setPartMesh: (mesh: PartMeshPayload | null) => void;
  setCapabilities: (capabilities: WorkspaceCapabilities) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendStatus: "starting",
  workspaceError: null,
  problems: [],
  activePartId: null,
  partMesh: null,
  capabilities: defaultCapabilities(),
  setBackendStatus: (status) => set({ backendStatus: status }),
  setWorkspaceError: (message) => set({ workspaceError: message }),
  setProblems: (problems) => set({ problems }),
  setActivePartId: (partId) => set({ activePartId: partId }),
  setPartMesh: (mesh) => set({ partMesh: mesh }),
  setCapabilities: (capabilities) => set({ capabilities }),
}));