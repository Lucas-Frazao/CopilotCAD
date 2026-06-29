/**
 * ============================================================================
 * FILE: syncAfterExecute.ts — Refresh UI state after chat executes a plan
 * ============================================================================
 *
 * After the user sends a modeling request, the app compiles intent (LLM → IR)
 * and executes steps on the backend. This module updates the global Zustand
 * store so panels show the right active part, problems list, and 3D mesh
 * without a full page reload. Feature F-011 / F-012.
 * ============================================================================
 */

// IPC bridge functions: thin wrappers around Electron preload APIs.
import { getPartMesh, getWorkspacePath } from "../ipc/bridge";
// Types for compile and execute RPC results.
import type { CompileIntentResult, ExecuteIntentResult } from "../ipc/types";
// Global app state (active part, mesh, problems, etc.).
import { useAppStore } from "../store/appStore";

/**
 * syncProjectStateAfterExecute — call after successful compile + execute pipeline.
 *
 * @param intent - Compile result (includes target part_id).
 * @param execution - Execute result (success, problems, final_step_id).
 */
export async function syncProjectStateAfterExecute(
  intent: CompileIntentResult,
  execution: ExecuteIntentResult,
): Promise<void> {
  // getState() reads Zustand store outside React components (no hook).
  const { setActivePartId, setProblems, setPartMesh } = useAppStore.getState();
  const partId = intent.target.part_id ?? null;

  // Always sync part selection and validation problems from execution.
  setActivePartId(partId);
  setProblems(execution.problems);

  // If execution failed or we lack part/step ids, skip mesh fetch.
  if (!execution.success || !partId || !execution.final_step_id) {
    return;
  }

  try {
    // Ask main process for current workspace folder path on disk.
    const workspacePath = await getWorkspacePath();
    // Fetch tessellated mesh for the part we just built.
    const mesh = await getPartMesh(workspacePath, partId);
    setPartMesh(mesh);
  } catch (err) {
    // Log for developers; clear mesh so viewport does not show stale geometry.
    console.error("Failed to load part mesh after execute:", err);
    setPartMesh(null);
  }
}
