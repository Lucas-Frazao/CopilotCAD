/**
 * ============================================================================
 * FILE: mesh-types.ts — 3D mesh data shapes for the viewport (F-011 / F-020)
 * ============================================================================
 *
 * The 3D viewport does not draw OCCT solids directly in the browser. The backend
 * tessellates (triangulates) geometry into flat arrays of numbers: vertex
 * positions, normals, and triangle indices. This file defines the TypeScript
 * shapes of those payloads sent over IPC to WebGL/React Three Fiber.
 *
 * F-011: single-part mesh. F-020: assembly with multiple instanced meshes.
 * ============================================================================
 */

/**
 * PartMeshPayload — triangle soup for one part's visible surface.
 */
export interface PartMeshPayload {
  // Flat [x,y,z, x,y,z, ...] vertex positions in model space.
  vertices: number[];
  // Per-vertex normal vectors for lighting (same flattening as vertices).
  normals: number[];
  // Triangle corner indices into the vertex array (groups of 3).
  indices: number[];
  // Optional: stable id per triangle for picking/highlighting faces.
  face_ids?: number[];
  // Optional: maps logical face names to lists of triangle ids.
  face_id_map?: Record<string, number[]>;
}

/**
 * AssemblyInstanceMesh — one part placed in an assembly with a transform.
 * Extends PartMeshPayload with instance/part ids and placement matrix.
 */
export interface AssemblyInstanceMesh extends PartMeshPayload {
  // Unique id for this placement in the assembly tree.
  instance_id: string;
  // Which part definition this instance references.
  part_id: string;
  // Legacy/alternate 16-element column-major transform (optional).
  transform?: number[];
  // Preferred 4×4 matrix as 16 floats (optional).
  matrix?: number[];
}

/**
 * AssemblyMeshPayload — all meshes needed to render an assembly at once.
 */
export interface AssemblyMeshPayload {
  meshes: AssemblyInstanceMesh[];
}
