import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("copilotcad", {
  ping: (): Promise<string> => ipcRenderer.invoke("copilotcad:rpc", "ping", {}) as Promise<string>,
  getWorkspacePath: (): Promise<string> =>
    ipcRenderer.invoke("copilotcad:getWorkspacePath") as Promise<string>,
  compileIntent: (
    message: string,
    context?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> =>
    ipcRenderer.invoke("copilotcad:rpc", "compile_intent", { message, context }) as Promise<
      Record<string, unknown>
    >,
  executeIntent: (ir: Record<string, unknown>): Promise<Record<string, unknown>> =>
    ipcRenderer.invoke("copilotcad:rpc", "execute_intent", { ir }) as Promise<
      Record<string, unknown>
    >,
  listWorkspaceTree: (workspacePath: string): Promise<unknown[]> =>
    ipcRenderer.invoke("copilotcad:rpc", "list_workspace_tree", {
      workspace_path: workspacePath,
    }) as Promise<unknown[]>,
  readWorkspaceFile: (
    workspacePath: string,
    relativePath: string,
  ): Promise<{ contents: string }> =>
    ipcRenderer.invoke("copilotcad:rpc", "read_workspace_file", {
      workspace_path: workspacePath,
      relative_path: relativePath,
    }) as Promise<{ contents: string }>,
});
