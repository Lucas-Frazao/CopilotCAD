import { app, BrowserWindow, ipcMain } from "electron";
import { spawn, ChildProcessWithoutNullStreams } from "child_process";
import * as fs from "fs";
import * as path from "path";

import { JsonRpcClient } from "./jsonrpc";

/** Health of the backend child process, surfaced to the renderer. */
type BackendStatus = "starting" | "ready" | "down";

/** Discriminated result returned to the renderer so structured error data
 *  (code/data) survives the IPC boundary without string-encoding hacks. */
type RpcEnvelope =
  | { ok: true; value: unknown }
  | { ok: false; error: { message: string; code?: number; data?: unknown } };

const MAX_RESTART_ATTEMPTS = 5;

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcessWithoutNullStreams | null = null;
let rpcClient: JsonRpcClient | null = null;
let backendStatus: BackendStatus = "starting";
let restartAttempts = 0;
let isQuitting = false;

function getProjectRoot(): string {
  return path.resolve(__dirname, "..", "..");
}

function getWorkspacePath(): string {
  const fromEnv = process.env.COPILOTCAD_WORKSPACE;
  if (fromEnv) {
    return path.resolve(fromEnv);
  }
  return path.join(getProjectRoot(), "example_project");
}

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

/** Push the current backend status to the renderer so it can show/clear a banner. */
function broadcastStatus(): void {
  mainWindow?.webContents.send("copilotcad:backend-status", backendStatus);
}

function setStatus(status: BackendStatus): void {
  backendStatus = status;
  broadcastStatus();
}

/**
 * Spawn the Python backend and wire a single JsonRpcClient to its stdio. Registers
 * exit/error handlers so a crash is detected (rather than hanging every request for
 * the full timeout) and, while the app is running, triggers a bounded auto-restart.
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

  // 'error' fires when spawn itself fails (e.g. python not found) — without this
  // handler Node would throw and crash the main process.
  proc.on("error", (err) => onGone(err instanceof Error ? err : new Error(String(err))));
  proc.on("exit", (code, signal) =>
    onGone(new Error(`Backend exited (code=${code ?? "null"}, signal=${signal ?? "null"})`)),
  );
}

/** Restart the backend a bounded number of times unless the app is shutting down. */
function maybeRestart(): void {
  if (isQuitting || restartAttempts >= MAX_RESTART_ATTEMPTS) {
    return;
  }
  restartAttempts += 1;
  console.warn(`[backend] restarting (attempt ${restartAttempts}/${MAX_RESTART_ATTEMPTS})`);
  spawnBackend();
}

async function pingBackend(): Promise<void> {
  if (!rpcClient) {
    return;
  }
  try {
    const result = await rpcClient.request("ping");
    restartAttempts = 0; // A successful ping means the backend is healthy again.
    setStatus("ready");
    console.log(`IPC ping → pong: ${JSON.stringify(result)}`);
  } catch (err) {
    console.error("IPC ping failed:", err);
    setStatus("down");
  }
}

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

  // Lock navigation down: the renderer is an app shell, not a browser. Block any
  // attempt to navigate away or open new windows (defence against injected links).
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (url !== devServerUrl) {
      event.preventDefault();
    }
  });

  // Send the latest status once the renderer has loaded.
  mainWindow.webContents.on("did-finish-load", broadcastStatus);

  if (devServerUrl) {
    mainWindow.loadURL(devServerUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(async () => {
  spawnBackend();

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
