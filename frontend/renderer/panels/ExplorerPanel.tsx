/**
 * ExplorerPanel.tsx — Project file tree browser
 *
 * Shows the on-disk workspace as a collapsible tree (parts/, exports/, docs/, …).
 * Clicking a file fetches its text via the backend and shows a read-only preview.
 * The backend owns all filesystem access — this panel never writes files directly.
 *
 * `refreshToken` is an integer the parent bumps after chat execute so the tree
 * refetches without remounting the whole panel.
 */

import { useCallback, useEffect, useRef, useState } from "react";

// Recursive tree UI — folders expand/collapse, files are selectable rows.
import FileTree from "../components/FileTree";
// IPC: listWorkspaceTree returns nested nodes; readWorkspaceFile returns file text.
import { listWorkspaceTree, readWorkspaceFile } from "../ipc/bridge";
import type { WorkspaceTreeNode } from "../ipc/types";

/** Props supplied by the App shell — absolute path to the open project folder. */
export interface ExplorerPanelProps {
  workspacePath: string;
  /** Increment to trigger a tree reload (e.g. after execute creates new files). */
  refreshToken?: number;
}

export default function ExplorerPanel({
  workspacePath,
  refreshToken = 0,
}: ExplorerPanelProps) {
  const [nodes, setNodes] = useState<WorkspaceTreeNode[]>([]);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  /**
   * Race guard for file preview reads.
   * If the user clicks file A then quickly clicks file B, A's slow response
   * must not overwrite B's preview — we compare requestId to the latest ref.
   */
  const previewRequestRef = useRef(0);

  /** Fetch the full workspace tree from the Python backend. */
  const loadTree = useCallback(async () => {
    if (!workspacePath) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const tree = await listWorkspaceTree(workspacePath);
      setNodes(tree);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setNodes([]);
    } finally {
      setLoading(false);
    }
  }, [workspacePath]);

  // Load on mount and whenever workspace path or refreshToken changes.
  useEffect(() => {
    void loadTree();
  }, [loadTree, refreshToken]);

  /** Toggle a folder open/closed by adding or removing its path from the Set. */
  const handleToggleExpand = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  /** Select a tree row; files trigger an async preview fetch. */
  const handleSelect = async (path: string, type: "file" | "dir") => {
    setSelectedPath(path);

    // Directories only update selection — no preview pane.
    if (type !== "file" || !workspacePath) {
      setPreviewText(null);
      return;
    }

    const requestId = ++previewRequestRef.current;
    try {
      const result = await readWorkspaceFile(workspacePath, path);
      if (requestId !== previewRequestRef.current) {
        return; // stale response — user already selected another file
      }
      setPreviewText(result.contents);
      setError(null);
    } catch (err) {
      if (requestId !== previewRequestRef.current) {
        return;
      }
      setPreviewText(null);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="explorer-panel">
      <div className="panel-placeholder">Explorer</div>
      <div className="explorer-body">
        {loading && <div className="explorer-status">Loading project tree…</div>}
        {error && <div className="explorer-error">{error}</div>}
        {!loading && nodes.length > 0 && (
          <FileTree
            nodes={nodes}
            selectedPath={selectedPath}
            expandedPaths={expandedPaths}
            onSelect={(path, type) => {
              void handleSelect(path, type);
            }}
            onToggleExpand={handleToggleExpand}
          />
        )}
        {previewText !== null && (
          <pre className="explorer-preview" data-testid="explorer-preview">
            {previewText}
          </pre>
        )}
      </div>
    </div>
  );
}
