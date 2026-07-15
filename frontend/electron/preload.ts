/**
 * ============================================================================
 * FILE: preload.ts — Secure bridge between renderer UI and Electron main process
 * ============================================================================
 *
 * Electron runs two worlds:
 *   1. Main process (Node.js) — can spawn Python, read files, etc.
 *   2. Renderer (web page) — sandboxed React app; NO direct Node access.
 *
 * preload.ts runs in a special middle layer. It uses contextBridge to expose a
 * small, typed API on window.copilotcad so React can call backend features
 * without breaking security (contextIsolation: true, nodeIntegration: false).
 * ============================================================================
 */

// contextBridge: safely publish APIs from preload to the renderer window.
// ipcRenderer: send messages to / receive from the main process.
import { contextBridge, ipcRenderer } from "electron";

/**
 * RpcEnvelope — every backend RPC returns this shape through main → preload → renderer.
 * The renderer bridge unwraps: ok → value, !ok → throw Error with code/data.
 */
type RpcEnvelope =
  | { ok: true; value: unknown }
  | { ok: false; error: { message: string; code?: number; data?: unknown } };

/**
 * rpc — helper that invokes the generic IPC channel copilotcad:rpc with a JSON-RPC method name.
 *
 * @param method - Backend method string (e.g. "compile_intent").
 * @param params - JSON-serializable parameters object.
 */
function rpc(method: string, params: Record<string, unknown> = {}): Promise<RpcEnvelope> {
  return ipcRenderer.invoke("copilotcad:rpc", method, params) as Promise<RpcEnvelope>;
}

/**
 * exposeInMainWorld — attaches window.copilotcad in the renderer.
 * Only the methods listed here are callable from React; nothing else from Node leaks.
 */
contextBridge.exposeInMainWorld("copilotcad", {
  /** Health check; returns envelope with string pong from Python backend. */
  ping: (): Promise<RpcEnvelope> => rpc("ping"),
  /** Absolute path to the open workspace folder (not an RPC envelope). */
  getWorkspacePath: (): Promise<string> =>
    ipcRenderer.invoke("copilotcad:getWorkspacePath") as Promise<string>,
  /** Current backend lifecycle: starting | ready | down. */
  getBackendStatus: (): Promise<string> =>
    ipcRenderer.invoke("copilotcad:getBackendStatus") as Promise<string>,
  /**
   * onBackendStatus — subscribe to push updates when backend health changes.
   * Returns an unsubscribe function the renderer should call on cleanup.
   */
  onBackendStatus: (callback: (status: string) => void): (() => void) => {
    const listener = (_event: unknown, status: string) => callback(status);
    ipcRenderer.on("copilotcad:backend-status", listener);
    return () => ipcRenderer.removeListener("copilotcad:backend-status", listener);
  },
  /** Send user chat text to backend LLM compile_intent. */
  compileIntent: (message: string, context?: Record<string, unknown>): Promise<RpcEnvelope> =>
    rpc("compile_intent", { message, context }),
  /** Run compiled Intent IR against the workspace on disk. */
  executeIntent: (
    ir: Record<string, unknown>,
    workspacePath: string,
  ): Promise<RpcEnvelope> =>
    rpc("execute_intent", { ir, workspace_path: workspacePath }),
  /** Tessellate a part for the 3D viewport. */
  getPartMesh: (workspacePath: string, partId: string): Promise<RpcEnvelope> =>
    rpc("get_part_mesh", { workspace_path: workspacePath, part_id: partId }),
  /** File tree for workspace explorer panel. */
  listWorkspaceTree: (workspacePath: string): Promise<RpcEnvelope> =>
    rpc("list_workspace_tree", { workspace_path: workspacePath }),
  /** Read a text file inside the workspace by relative path. */
  readWorkspaceFile: (workspacePath: string, relativePath: string): Promise<RpcEnvelope> =>
    rpc("read_workspace_file", {
      workspace_path: workspacePath,
      relative_path: relativePath,
    }),
});
