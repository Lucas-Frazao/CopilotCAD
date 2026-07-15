/**
 * ============================================================================
 * FILE: FileTree.tsx — Recursive workspace file/folder tree (F-009)
 * ============================================================================
 *
 * Renders WorkspaceTreeNode data from list_workspace_tree RPC. Supports
 * expand/collapse for directories and selection highlight for the active path.
 * Used by ExplorerPanel on the left side of the app.
 * ============================================================================
 */

import type { WorkspaceTreeNode } from "../ipc/types";

export interface FileTreeProps {
  nodes: WorkspaceTreeNode[];
  selectedPath: string | null;
  expandedPaths: Set<string>;
  onSelect: (path: string, type: "file" | "dir") => void;
  onToggleExpand: (path: string) => void;
}

/**
 * FileTreeNode — recursive inner component; depth controls left padding indent.
 */
function FileTreeNode({
  node,
  selectedPath,
  expandedPaths,
  onSelect,
  onToggleExpand,
  depth,
}: {
  node: WorkspaceTreeNode;
  selectedPath: string | null;
  expandedPaths: Set<string>;
  onSelect: (path: string, type: "file" | "dir") => void;
  onToggleExpand: (path: string) => void;
  depth: number;
}) {
  const isDir = node.type === "dir";
  const isExpanded = isDir && expandedPaths.has(node.path);
  const isSelected = selectedPath === node.path;

  if (isDir) {
    return (
      <div className="file-tree-node">
        <button
          type="button"
          className={`file-tree-row file-tree-dir${isSelected ? " is-selected" : ""}`}
          style={{ paddingLeft: `${8 + depth * 12}px` }}
          aria-label={`expand ${node.name}`}
          onClick={() => onToggleExpand(node.path)}
        >
          <span className="file-tree-chevron">{isExpanded ? "▾" : "▸"}</span>
          <span className="file-tree-label">{node.name}</span>
        </button>
        {isExpanded &&
          (node.children ?? []).map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              selectedPath={selectedPath}
              expandedPaths={expandedPaths}
              onSelect={onSelect}
              onToggleExpand={onToggleExpand}
              depth={depth + 1}
            />
          ))}
      </div>
    );
  }

  return (
    <button
      type="button"
      className={`file-tree-row file-tree-file${isSelected ? " is-selected" : ""}`}
      style={{ paddingLeft: `${20 + depth * 12}px` }}
      aria-label={node.name}
      onClick={() => onSelect(node.path, "file")}
    >
      <span className="file-tree-label">{node.name}</span>
    </button>
  );
}

/**
 * FileTree — maps top-level nodes to FileTreeNode at depth 0.
 */
export default function FileTree({
  nodes,
  selectedPath,
  expandedPaths,
  onSelect,
  onToggleExpand,
}: FileTreeProps) {
  return (
    <div className="file-tree">
      {nodes.map((node) => (
        <FileTreeNode
          key={node.path}
          node={node}
          selectedPath={selectedPath}
          expandedPaths={expandedPaths}
          onSelect={onSelect}
          onToggleExpand={onToggleExpand}
          depth={0}
        />
      ))}
    </div>
  );
}
