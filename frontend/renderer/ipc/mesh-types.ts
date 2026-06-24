/** Mesh payload types for viewport (F-011 / F-020). */

export interface PartMeshPayload {
  vertices: number[];
  normals: number[];
  indices: number[];
  face_ids?: number[];
  face_id_map?: Record<string, number[]>;
}

export interface AssemblyInstanceMesh extends PartMeshPayload {
  instance_id: string;
  part_id: string;
  transform?: number[];
  matrix?: number[];
}

export interface AssemblyMeshPayload {
  meshes: AssemblyInstanceMesh[];
}
