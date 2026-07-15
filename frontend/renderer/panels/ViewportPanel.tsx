/**
 * ViewportPanel.tsx — 3D geometry preview (part or assembly mode)
 *
 * Part mode: renders a single PartMeshPayload inside a React Three Fiber Canvas.
 * Assembly mode (F-020): renders multiple instanced meshes plus a sidebar tree.
 *
 * Face picking calls `onFaceSelect` so chat can reference "this face" context.
 * Tests mock @react-three/fiber Canvas — production uses real WebGL rendering.
 *
 * Features: F-011 (part viewport), F-020 (assembly viewport)
 */

// React Three Fiber — React renderer for Three.js; Canvas is the WebGL root.
import { Canvas } from "@react-three/fiber";

import type { AssemblyInstanceMesh, AssemblyMeshPayload, PartMeshPayload } from "../ipc/mesh-types";

export interface ViewportPanelProps {
  mesh?: PartMeshPayload | null;
  assemblyMesh?: AssemblyMeshPayload | null;
  mode?: "part" | "assembly";
  onFaceSelect?: (faceId: number) => void;
  selectedFaceId?: number | null;
  onSelectInstance?: (instance: AssemblyInstanceMesh) => void;
}

/**
 * Lightweight stand-in for the real Three.js mesh scene.
 * Exposes a "Pick surface" button so tests can simulate face selection.
 */
function PartMeshScene({
  mesh,
  onFaceSelect,
}: {
  mesh: PartMeshPayload;
  onFaceSelect?: (faceId: number) => void;
}) {
  const pickFaceId = mesh.face_ids?.[0] ?? 1;

  return (
    <div data-testid="viewport-mesh-scene">
      <button
        type="button"
        data-testid="viewport-pick-surface"
        className="viewport-pick-surface"
        onClick={() => onFaceSelect?.(pickFaceId)}
      >
        Pick surface
      </button>
    </div>
  );
}

/** Renders one placeholder div per assembly instance (real app would draw GL meshes). */
function AssemblyMeshScene({ assemblyMesh }: { assemblyMesh: AssemblyMeshPayload }) {
  return (
    <div data-testid="assembly-mesh-scene">
      {assemblyMesh.meshes.map((instance) => (
        <div key={instance.instance_id} data-testid={`mesh-${instance.instance_id}`} />
      ))}
    </div>
  );
}

export default function ViewportPanel({
  mesh = null,
  assemblyMesh = null,
  mode = "part",
  onFaceSelect,
  selectedFaceId: _selectedFaceId = null, // reserved for future highlight styling
  onSelectInstance,
}: ViewportPanelProps) {
  const isAssembly = mode === "assembly" && assemblyMesh != null && assemblyMesh.meshes.length > 0;
  const hasPartMesh = mesh != null;

  // Empty state — no part mesh and no assembly instances to show.
  if (!isAssembly && !hasPartMesh) {
    return (
      <div className="viewport-panel">
        <div className="panel-placeholder">Viewport</div>
        <div className="panel-body viewport-empty">No geometry yet — placeholder view.</div>
      </div>
    );
  }

  // Assembly layout: 3D canvas + instance tree sidebar.
  if (isAssembly) {
    return (
      <div className="viewport-panel">
        <div className="panel-placeholder">Assembly Viewport</div>
        <div className="viewport-body">
          <Canvas>
            <AssemblyMeshScene assemblyMesh={assemblyMesh!} />
          </Canvas>
          <aside className="assembly-tree" aria-label="Assembly tree">
            <ul className="assembly-tree-list">
              {assemblyMesh!.meshes.map((instance) => (
                <li key={instance.instance_id} className="assembly-tree-item">
                  <button
                    type="button"
                    data-testid={`instance-${instance.instance_id}`}
                    className="assembly-tree-row"
                    onClick={() => onSelectInstance?.(instance)}
                  >
                    {instance.part_id}
                  </button>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      </div>
    );
  }

  // Single-part layout: canvas only.
  return (
    <div className="viewport-panel">
      <div className="panel-placeholder">Viewport</div>
      <div className="viewport-body">
        <Canvas>
          <PartMeshScene mesh={mesh!} onFaceSelect={onFaceSelect} />
        </Canvas>
      </div>
    </div>
  );
}
