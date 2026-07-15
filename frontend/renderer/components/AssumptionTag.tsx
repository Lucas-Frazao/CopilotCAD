/**
 * ============================================================================
 * FILE: AssumptionTag.tsx — Inline UI chip for one design assumption (F-023)
 * ============================================================================
 *
 * When the AI makes a guess (e.g. "hole diameter 6 mm"), it appears as a tag
 * in chat. The user can Confirm, Reject, or Edit. Changes call updateAssumption
 * over IPC so the backend persists status on the part folder.
 * ============================================================================
 */

import { useState } from "react";

import { updateAssumption } from "../ipc/bridge";
import type { IRAssumptionPayload } from "../ipc/types";

/** Props passed from ChatMessage when rendering an assumption list. */
interface AssumptionTagProps {
  assumption: IRAssumptionPayload;
  partId?: string;
  onUpdated?: () => void;
}

/**
 * AssumptionTag — small interactive badge with optional action buttons.
 */
export default function AssumptionTag({ assumption, partId, onUpdated }: AssumptionTagProps) {
  const importance = assumption.importance ?? "medium";
  const [status, setStatus] = useState(assumption.status ?? "proposed");
  const [text, setText] = useState(assumption.text);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(assumption.text);

  // Only proposed assumptions on a known part show Confirm/Reject/Edit.
  const isProposed = status === "proposed" && partId != null;

  const handleConfirm = () => {
    if (!partId) {
      return;
    }
    setStatus("confirmed");
    onUpdated?.();
    void updateAssumption(partId, assumption.id, "confirmed", undefined);
  };

  const handleReject = async () => {
    if (!partId) {
      return;
    }
    await updateAssumption(partId, assumption.id, "rejected", undefined);
    setStatus("rejected");
    onUpdated?.();
  };

  const handleSaveEdit = async () => {
    if (!partId) {
      return;
    }
    await updateAssumption(partId, assumption.id, "proposed", editText);
    setText(editText);
    setEditing(false);
    onUpdated?.();
  };

  return (
    <span className={`assumption-tag assumption-tag-${importance} assumption-status-${status}`}>
      {editing ? (
        <span className="assumption-tag-edit">
          <input
            className="assumption-tag-input"
            type="text"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
          />
          <button type="button" className="assumption-tag-save" onClick={handleSaveEdit}>
            Save
          </button>
        </span>
      ) : (
        <span className="assumption-tag-text">{text}</span>
      )}
      <span className="assumption-tag-badge">{status}</span>
      {isProposed && !editing && (
        <span className="assumption-tag-actions">
          <button type="button" className="assumption-tag-confirm" onClick={handleConfirm}>
            Confirm
          </button>
          <button type="button" className="assumption-tag-reject" onClick={handleReject}>
            Reject
          </button>
          <button type="button" className="assumption-tag-edit-btn" onClick={() => setEditing(true)}>
            Edit
          </button>
        </span>
      )}
    </span>
  );
}
