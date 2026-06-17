import type { CopilotCADApi } from "./types";

declare global {
  interface Window {
    copilotcad?: CopilotCADApi;
  }
}

export {};
