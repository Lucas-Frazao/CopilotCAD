/**
 * ============================================================================
 * FILE: app.tsx — Root React layout for CopilotCAD
 * ============================================================================
 *
 * This component is the top-level UI shell: three columns (explorer, 3D viewport,
 * chat). It wires global concerns — backend health banner, workspace path, and
 * refreshing the file tree when chat changes the project.
 * ============================================================================
 */

// Global styles for layout, panels, banners.
import "./app.css";

// useEffect runs side effects after render; useState holds local component state.
import { useEffect, useState } from "react";

// IPC helpers to read backend status and workspace path from main process.
import { getBackendStatus, getWorkspacePath, onBackendStatus } from "./ipc/bridge";
// Shared Zustand store for mesh and error banners used by multiple panels.
import { useAppStore } from "./store/appStore";
import ExplorerPanel from "./panels/ExplorerPanel";
import ViewportPanel from "./panels/ViewportPanel";
import ChatPanel from "./panels/ChatPanel";

/**
 * App — default export mounted by main.tsx inside React.StrictMode.
 */
export default function App() {
  // Local state: path string and a counter to force ExplorerPanel refresh.
  const [workspacePath, setWorkspacePath] = useState("");
  const [explorerRefreshToken, setExplorerRefreshToken] = useState(0);

  // Subscribe to slices of global store (re-render when these change).
  const backendStatus = useAppStore((s) => s.backendStatus);
  const workspaceError = useAppStore((s) => s.workspaceError);
  const partMesh = useAppStore((s) => s.partMesh);
  const setBackendStatus = useAppStore((s) => s.setBackendStatus);
  const setWorkspaceError = useAppStore((s) => s.setWorkspaceError);

  /**
   * On mount: read initial backend status and subscribe to push updates.
   * Cleanup returns unsubscribe so we do not leak listeners.
   */
  useEffect(() => {
    getBackendStatus()
      .then(setBackendStatus)
      .catch(() => setBackendStatus("down"));
    const unsubscribe = onBackendStatus(setBackendStatus);
    return unsubscribe;
  }, [setBackendStatus]);

  /**
   * On mount: resolve workspace folder path from main process.
   * Failures go to workspaceError for the red banner.
   */
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
      {/* role="alert" helps screen readers announce backend outage. */}
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
          <ViewportPanel mesh={partMesh} />
        </main>
        <aside className="panel-column panel-column-right">
          <ChatPanel
            onWorkspaceChanged={() => {
              // Bump token so ExplorerPanel refetches tree after chat mutations.
              setExplorerRefreshToken((token) => token + 1);
            }}
          />
        </aside>
      </div>
    </div>
  );
}
