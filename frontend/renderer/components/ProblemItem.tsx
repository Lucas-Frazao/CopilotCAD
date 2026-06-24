import type { ProblemPayload } from "../ipc/types";

export interface ProblemItemProps {
  problem: ProblemPayload;
  onClick?: (problem: ProblemPayload) => void;
}

export default function ProblemItem({ problem, onClick }: ProblemItemProps) {
  const steps = problem.suggested_next_steps ?? [];

  return (
    <li
      className={`problem-item problem-item-${problem.severity}`}
      role="listitem"
      onClick={() => onClick?.(problem)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.(problem);
        }
      }}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="problem-item-header">
        <span className="problem-item-type">{problem.type}</span>
        <span className={`problem-item-severity problem-severity-${problem.severity}`}>
          {problem.severity}
        </span>
      </div>
      <div className="problem-item-message">{problem.message}</div>
      {steps.length > 0 && (
        <ul className="problem-item-steps">
          {steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      )}
    </li>
  );
}