import type { CopilotCADApi, CompileIntentResult } from "./types";

function getApi(): CopilotCADApi {
  if (typeof window === "undefined" || !window.copilotcad) {
    throw new Error("CopilotCAD IPC is only available in the Electron renderer");
  }
  return window.copilotcad;
}

export async function ping(): Promise<string> {
  return getApi().ping();
}

export async function compileIntent(
  message: string,
  context?: Record<string, unknown>,
): Promise<CompileIntentResult> {
  return getApi().compileIntent(message, context);
}
