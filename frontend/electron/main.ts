/**
 * ============================================================================
 * FILE: main.ts — Electron main process entry (window + Python backend)
 * ============================================================================
 *
 * This is the "desktop app brain" that:
 *   1. Spawns the Python JSON-RPC backend as a child process
 *   2. Routes IPC from the React UI to JSON-RPC on stdin/stdout
 *   3. Creates the BrowserWindow with secure webPreferences
 *   4. Restarts the backend on crash (bounded retries)
 *
 * The renderer never talks to Python directly — only through ipcMain handlers here.
 * ============================================================================
 */

// app: Electron application lifecycle. BrowserWindow: native window. ipcMain: IPC server.
import { app, BrowserWindow, ipcMain } from "electron";
// spawn: start child process. ChildProcessWithoutNullStreams: typed stdin/stdout/stderr pipes.
import { spawn, ChildProcessWithoutNullStreams } from "child_process";
import * as fs from "fs";
import * as path from "path";

import { JsonRpcClient } from "./jsonrpc";

/** Health of the backend child process, surfaced to the renderer. */
type BackendStatus = "starting" | "ready" | "down";

/**
 * RpcEnvelope — discriminated union returned to renderer over IPC.
 * Structured error code/data survive the boundary without string-encoding hacks.
 */
type RpcEnvelope =
  | { ok: true; value: unknown }
  | { ok: false; error: { message: string; code?: number; data?: unknown } };

/** Max automatic backend respawns before giving up (while app stays open). */
const MAX_RESTART_ATTEMPTS = 5;

// Module-level singletons for the one main window and one backend child.
let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcessWithoutNullStreams | null = null;
let rpcClient: JsonRpcClient | null = null;
let backendStatus: BackendStatus = "starting";
let restartAttempts = 0;
let isQuitting = false;

/** Repo root: two levels up from compiled electron output (frontend/dist-electron). */
function getProjectRoot(): string {
  return path.resolve(__dirname, "..", "..");
}

/**
 * getWorkspacePath — folder containing copilotcad.json and parts/.
 * Override with COPILOTCAD_WORKSPACE env var for development.
 */
function getWorkspacePath(): string {
  const fromEnv = process.env.COPILOTCAD_WORKSPACE;
  if (fromEnv) {
    return path.resolve(fromEnv);
  }
  return path.join(getProjectRoot(), "example_project");
}

/**
 * getPythonExecutable — resolve venv python or fall back to system python.
 * COPILOTCAD_PYTHON env can point to a specific interpreter.
 */
function getPythonExecutable(backendDir: string): string {
  const fromEnv = process.env.COPILOTCAD_PYTHON;
  if (fromEnv && fs.existsSync(fromEnv)) {
    return path.resolve(fromEnv);
  }

  const venvPython =
    process.platform === "win32"
      ? path.join(backendDir, ".venv", "Scripts", "python.exe")
      : path.join(backendDir, ".venv", "bin", "python");

  if (fs.existsSync(venvPython)) {
    return venvPython;
  }

  return process.platform === "win32" ? "python" : "python3";
}

/** broadcastStatus — push current backendStatus to renderer via preload channel. */
function broadcastStatus(): void {
  mainWindow?.webContents.send("copilotcad:backend-status", backendStatus);
}

function setStatus(status: BackendStatus): void {
  backendStatus = status;
  broadcastStatus();
}

/**
 * spawnBackend — start Python main.py and wire JsonRpcClient to its stdio.
 * Registers exit/error handlers for crash detection and bounded auto-restart.
 */
function spawnBackend(): void {
  const projectRoot = getProjectRoot();
  const backendDir = path.join(projectRoot, "backend");
  const python = getPythonExecutable(backendDir);

  setStatus("starting");

  const proc = spawn(python, ["main.py"], {
    cwd: backendDir,
    stdio: ["pipe", "pipe", "pipe"],
  });
  backendProcess = proc;

  const client = new JsonRpcClient({
    send: (line: string) => proc.stdin.write(line),
  });
  rpcClient = client;

  // Every stdout chunk goes to the single client's line buffer.
  proc.stdout.on("data", (chunk: Buffer) => client.receive(chunk));
  proc.stderr.on("data", (data: Buffer) => {
    console.error("[backend stderr]", data.toString());
  });

  const onGone = (reason: Error) => {
    if (rpcClient === client) {
      client.handleClose(reason);
      setStatus("down");
      maybeRestart();
    }
  };

  // 'error' fires when spawn itself fails (e.g. python not found).
  proc.on("error", (err) => onGone(err instanceof Error ? err : new Error(String(err))));
  proc.on("exit", (code, signal) =>
    onGone(new Error(`Backend exited (code=${code ?? "null"}, signal=${signal ?? "null"})`)),
  );
}

/** maybeRestart — respawn backend unless shutting down or max attempts reached. */
function maybeRestart(): void {
  if (isQuitting || restartAttempts >= MAX_RESTART_ATTEMPTS) {
    return;
  }
  restartAttempts += 1;
  console.warn(`[backend] restarting (attempt ${restartAttempts}/${MAX_RESTART_ATTEMPTS})`);
  spawnBackend();
}

/** pingBackend — verify JSON-RPC path works; sets status ready on success. */
async function pingBackend(): Promise<void> {
  if (!rpcClient) {
    return;
  }
  try {
    const result = await rpcClient.request("ping");
    restartAttempts = 0;
    setStatus("ready");
    console.log(`IPC ping → pong: ${JSON.stringify(result)}`);
  } catch (err) {
    console.error("IPC ping failed:", err);
    setStatus("down");
  }
}

/** createWindow — open the main BrowserWindow loading Vite dev URL or built HTML. */
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;

  // Block navigation and new windows — renderer is an app shell, not a browser.
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (url !== devServerUrl) {
      event.preventDefault();
    }
  });

  mainWindow.webContents.on("did-finish-load", broadcastStatus);

  if (devServerUrl) {
    mainWindow.loadURL(devServerUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

// Electron app is ready — register IPC, spawn backend, open window.
app.whenReady().then(async () => {
  spawnBackend();

  /**
   * copilotcad:rpc — generic channel: renderer sends method + params,
   * main forwards to JsonRpcClient and wraps result in RpcEnvelope.
   */
  ipcMain.handle(
    "copilotcad:rpc",
    async (_event, method: string, params: unknown): Promise<RpcEnvelope> => {
      if (!rpcClient || rpcClient.isClosed) {
        return {
          ok: false,
          error: { message: "Backend process is not running", data: { error_type: "backend_down" } },
        };
      }
      try {
        const value = await rpcClient.request(method, params);
        return { ok: true, value };
      } catch (err) {
        const rpcErr = err as { message?: string; code?: number; data?: unknown };
        return {
          ok: false,
          error: { message: rpcErr.message ?? "JSON-RPC error", code: rpcErr.code, data: rpcErr.data },
        };
      }
    },
  );

  ipcMain.handle("copilotcad:getWorkspacePath", () => getWorkspacePath());
  ipcMain.handle("copilotcad:getBackendStatus", () => backendStatus);

  await pingBackend();
  createWindow();
});

app.on("before-quit", () => {
  isQuitting = true;
});

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
    rpcClient = null;
  }

  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
