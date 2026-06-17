import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("copilotcad", {
  ping: (): Promise<string> => ipcRenderer.invoke("copilotcad:rpc", "ping", {}) as Promise<string>,
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
});
