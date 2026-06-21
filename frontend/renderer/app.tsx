import "./app.css";

import { useEffect, useState } from "react";

import { getBackendStatus, getWorkspacePath, onBackendStatus } from "./ipc/bridge";
import { useAppStore } from "./store/appStore";
import ExplorerPanel from "./panels/ExplorerPanel";
import ViewportPanel from "./panels/ViewportPanel";
import ChatPanel from "./panels/ChatPanel";

export default function App() {
  const [workspacePath, setWorkspacePath] = useState("");
  const [explorerRefreshToken, setExplorerRefreshToken] = useState(0);

  const backendStatus = useAppStore((s) => s.backendStatus);
  const workspaceError = useAppStore((s) => s.workspaceError);
  const setBackendStatus = useAppStore((s) => s.setBackendStatus);
  const setWorkspaceError = useAppStore((s) => s.setWorkspaceError);

  // Track backend health so the UI can show a banner instead of silently hanging
  // when the backend process is down.
  useEffect(() => {
    getBackendStatus()
      .then(setBackendStatus)
      .catch(() => setBackendStatus("down"));
    const unsubscribe = onBackendStatus(setBackendStatus);
    return unsubscribe;
  }, [setBackendStatus]);

  useEffect(() => {
    getWorkspacePath()
      .then((path) => {
        setWorkspacePath(path);
        setWorkspaceError(null);
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : String(err);
        console.error("Failed to resolve workspace path:", err);
        setWorkspaceError(message);
      });
  }, [setWorkspaceError]);

  return (
    <div className="app-shell">
      {backendStatus === "down" && (
        <div className="app-banner app-banner-error" role="alert">
          Backend is not responding. Some actions are unavailable while it restarts.
        </div>
      )}
      {workspaceError && (
        <div className="app-banner app-banner-error" role="alert">
          Could not open the workspace: {workspaceError}
        </div>
      )}
      <div className="app-columns">
        <aside className="panel-column panel-column-left">
          <ExplorerPanel
            workspacePath={workspacePath}
            refreshToken={explorerRefreshToken}
          />
        </aside>
        <main className="panel-column panel-column-center">
          <ViewportPanel />
        </main>
        <aside className="panel-column panel-column-right">
          <ChatPanel
            onWorkspaceChanged={() => {
              setExplorerRefreshToken((token) => token + 1);
            }}
          />
        </aside>
      </div>
    </div>
  );
}
