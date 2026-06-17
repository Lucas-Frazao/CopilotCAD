import { app, BrowserWindow } from "electron";
import { spawn, ChildProcessWithoutNullStreams } from "child_process";
import * as fs from "fs";
import * as path from "path";

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcessWithoutNullStreams | null = null;

function getProjectRoot(): string {
  return path.resolve(__dirname, "..", "..");
}

function getPythonExecutable(backendDir: string): string {
  const venvPython =
    process.platform === "win32"
      ? path.join(backendDir, ".venv", "Scripts", "python.exe")
      : path.join(backendDir, ".venv", "bin", "python");

  if (fs.existsSync(venvPython)) {
    return venvPython;
  }

  return process.platform === "win32" ? "python" : "python3";
}

function spawnBackend(): ChildProcessWithoutNullStreams {
  const projectRoot = getProjectRoot();
  const backendDir = path.join(projectRoot, "backend");
  const python = getPythonExecutable(backendDir);

  const proc = spawn(python, ["main.py"], {
    cwd: backendDir,
    stdio: ["pipe", "pipe", "pipe"],
  });

  proc.stderr.on("data", (data: Buffer) => {
    console.error("[backend stderr]", data.toString());
  });

  return proc;
}

function sendJsonRpc(
  proc: ChildProcessWithoutNullStreams,
  method: string,
  params: unknown = {},
  id = 1,
): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const request =
      JSON.stringify({
        jsonrpc: "2.0",
        id,
        method,
        params,
      }) + "\n";

    let buffer = "";

    const onData = (chunk: Buffer) => {
      buffer += chunk.toString();
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
          const response = JSON.parse(line) as {
            id?: number;
            result?: unknown;
            error?: unknown;
          };

          if (response.id === id) {
            proc.stdout.off("data", onData);
            clearTimeout(timeout);

            if (response.error) {
              reject(response.error);
            } else {
              resolve(response.result);
            }
            return;
          }
        } catch {
          // Ignore non-JSON lines until a full message is received.
        }
      }
    };

    const timeout = setTimeout(() => {
      proc.stdout.off("data", onData);
      reject(new Error("JSON-RPC request timed out"));
    }, 10000);

    proc.stdout.on("data", onData);
    proc.stdin.write(request);
  });
}

async function pingBackend(): Promise<void> {
  backendProcess = spawnBackend();

  try {
    const result = await sendJsonRpc(backendProcess, "ping");
    console.log(`IPC ping → pong: ${JSON.stringify(result)}`);
  } catch (err) {
    console.error("IPC ping failed:", err);
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

  if (devServerUrl) {
    mainWindow.loadURL(devServerUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(async () => {
  await pingBackend();
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill();
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
