import { contextBridge, ipcRenderer } from "electron";

/** Result envelope returned by the main process for every backend RPC. The
 *  renderer-side bridge unwraps it: `ok` → value, otherwise throw with code/data. */
type RpcEnvelope = { ok: true; value: unknown } | { ok: false; error: { message: string; code?: number; data?: unknown } };

function rpc(method: string, params: Record<string, unknown> = {}): Promise<RpcEnvelope> {
  return ipcRenderer.invoke("copilotcad:rpc", method, params) as Promise<RpcEnvelope>;
}

contextBridge.exposeInMainWorld("copilotcad", {
  ping: (): Promise<RpcEnvelope> => rpc("ping"),
  getWorkspacePath: (): Promise<string> =>
    ipcRenderer.invoke("copilotcad:getWorkspacePath") as Promise<string>,
  getBackendStatus: (): Promise<string> =>
    ipcRenderer.invoke("copilotcad:getBackendStatus") as Promise<string>,
  onBackendStatus: (callback: (status: string) => void): (() => void) => {
    const listener = (_event: unknown, status: string) => callback(status);
    ipcRenderer.on("copilotcad:backend-status", listener);
    return () => ipcRenderer.removeListener("copilotcad:backend-status", listener);
  },
  compileIntent: (message: string, context?: Record<string, unknown>): Promise<RpcEnvelope> =>
    rpc("compile_intent", { message, context }),
  executeIntent: (ir: Record<string, unknown>): Promise<RpcEnvelope> =>
    rpc("execute_intent", { ir }),
  listWorkspaceTree: (workspacePath: string): Promise<RpcEnvelope> =>
    rpc("list_workspace_tree", { workspace_path: workspacePath }),
  readWorkspaceFile: (workspacePath: string, relativePath: string): Promise<RpcEnvelope> =>
    rpc("read_workspace_file", {
      workspace_path: workspacePath,
      relative_path: relativePath,
    }),
});
