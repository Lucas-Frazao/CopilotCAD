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
  selectedFaceId: _selectedFaceId = null,
  onSelectInstance,
}: ViewportPanelProps) {
  const isAssembly = mode === "assembly" && assemblyMesh != null && assemblyMesh.meshes.length > 0;
  const hasPartMesh = mesh != null;

  if (!isAssembly && !hasPartMesh) {
    return (
      <div className="viewport-panel">
        <div className="panel-placeholder">Viewport</div>
        <div className="panel-body viewport-empty">No geometry yet — placeholder view.</div>
      </div>
    );
  }

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