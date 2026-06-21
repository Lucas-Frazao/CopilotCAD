import { create } from "zustand";

import type { BackendStatus } from "../ipc/types";

/**
 * Global UI state that several panels need to react to: backend health and any
 * failure to resolve the workspace. Previously every panel kept this in local
 * state, so an IPC failure (e.g. backend down) had no shared place to surface.
 */
interface AppState {
  backendStatus: BackendStatus;
  workspaceError: string | null;
  setBackendStatus: (status: BackendStatus) => void;
  setWorkspaceError: (message: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendStatus: "starting",
  workspaceError: null,
  setBackendStatus: (status) => set({ backendStatus: status }),
  setWorkspaceError: (message) => set({ workspaceError: message }),
}));
