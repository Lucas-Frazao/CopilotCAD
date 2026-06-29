/**
 * ============================================================================
 * FILE: appStore.ts — Global Zustand store for cross-panel UI state
 * ============================================================================
 *
 * Zustand is a small state library. Multiple panels (viewport, problems, chat)
 * need the same data: which part is active, current mesh, backend health, etc.
 * This store is the single shared place instead of duplicating useState in each panel.
 * ============================================================================
 */

// create builds a React hook (useAppStore) backed by a global store.
import { create } from "zustand";

// Edition limits defaults and type.
import { defaultCapabilities, type WorkspaceCapabilities } from "../capabilities/workspaceCapabilities";
import type { PartMeshPayload } from "../ipc/mesh-types";
import type { BackendStatus, ProblemPayload } from "../ipc/types";

/**
 * AppState — everything held in the store plus setter functions.
 *
 * Setters are colocated so components call useAppStore(s => s.setProblems) etc.
 */
interface AppState {
  // Python backend: starting → ready, or down on crash.
  backendStatus: BackendStatus;
  // Message when workspace path cannot be resolved (shown in UI).
  workspaceError: string | null;
  // Problems panel rows from last execute or project scan.
  problems: ProblemPayload[];
  // Which part id is selected for mesh/history/etc.
  activePartId: string | null;
  // Latest mesh payload for ViewportPanel (null = empty viewport).
  partMesh: PartMeshPayload | null;
  // Workspace edition caps (parts limit, export flags).
  capabilities: WorkspaceCapabilities;
  setBackendStatus: (status: BackendStatus) => void;
  setWorkspaceError: (message: string | null) => void;
  setProblems: (problems: ProblemPayload[]) => void;
  setActivePartId: (partId: string | null) => void;
  setPartMesh: (mesh: PartMeshPayload | null) => void;
  setCapabilities: (capabilities: WorkspaceCapabilities) => void;
}

/**
 * useAppStore — React hook. Example: const mesh = useAppStore(s => s.partMesh);
 *
 * (set) => ({...}) is Zustand's initializer: set merges partial state updates.
 */
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
