import "./app.css";

import ExplorerPanel from "./panels/ExplorerPanel";
import ViewportPanel from "./panels/ViewportPanel";
import ChatPanel from "./panels/ChatPanel";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="panel-column panel-column-left">
        <ExplorerPanel />
      </aside>
      <main className="panel-column panel-column-center">
        <ViewportPanel />
      </main>
      <aside className="panel-column panel-column-right">
        <ChatPanel />
      </aside>
    </div>
  );
}
