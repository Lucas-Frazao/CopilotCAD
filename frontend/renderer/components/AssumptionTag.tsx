import type { IRAssumptionPayload } from "../ipc/types";

interface AssumptionTagProps {
  assumption: IRAssumptionPayload;
}

export default function AssumptionTag({ assumption }: AssumptionTagProps) {
  const importance = assumption.importance ?? "medium";
  const status = assumption.status ?? "proposed";

  return (
    <span className={`assumption-tag assumption-tag-${importance} assumption-status-${status}`}>
      <span className="assumption-tag-text">{assumption.text}</span>
      <span className="assumption-tag-badge">{status}</span>
    </span>
  );
}
