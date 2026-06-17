import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("copilotcad", {});
