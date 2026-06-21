import { useCallback, useEffect, useRef, useState } from "react";

import FileTree from "../components/FileTree";
import { listWorkspaceTree, readWorkspaceFile } from "../ipc/bridge";
import type { WorkspaceTreeNode } from "../ipc/types";

export interface ExplorerPanelProps {
  workspacePath: string;
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
  // Monotonic token so an earlier, slower file read cannot overwrite the preview
  // of a file selected later (out-of-order resolution on rapid clicks).
  const previewRequestRef = useRef(0);

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

  useEffect(() => {
    void loadTree();
  }, [loadTree, refreshToken]);

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

  const handleSelect = async (path: string, type: "file" | "dir") => {
    setSelectedPath(path);

    if (type !== "file" || !workspacePath) {
      setPreviewText(null);
      return;
    }

    const requestId = ++previewRequestRef.current;
    try {
      const result = await readWorkspaceFile(workspacePath, path);
      // Drop the result if a newer selection has superseded this request.
      if (requestId !== previewRequestRef.current) {
        return;
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
