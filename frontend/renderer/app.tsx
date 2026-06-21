import "./app.css";

import { useEffect, useState } from "react";

import { getWorkspacePath } from "./ipc/bridge";
import ExplorerPanel from "./panels/ExplorerPanel";
import ViewportPanel from "./panels/ViewportPanel";
import ChatPanel from "./panels/ChatPanel";

export default function App() {
  const [workspacePath, setWorkspacePath] = useState("");
  const [explorerRefreshToken, setExplorerRefreshToken] = useState(0);

  useEffect(() => {
    getWorkspacePath()
      .then(setWorkspacePath)
      .catch((err) => {
        console.error("Failed to resolve workspace path:", err);
      });
  }, []);

  return (
    <div className="app-shell">
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
  );
}
