import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProblemsPanel from "./ProblemsPanel";
import type { ProblemPayload } from "../ipc/types";

const SAMPLE_PROBLEMS: ProblemPayload[] = [
  {
    id: "p1",
    type: "unresolved_assumption",
    severity: "warning",
    message: "High-importance assumption is still proposed.",
    part_id: "mounting_plate",
    suggested_next_steps: ["Confirm assumption in chat."],
  },
  {
    id: "p2",
    type: "missing_required_input",
    severity: "blocking",
    message: "Blocking question is unanswered.",
    suggested_next_steps: ["Answer the question in chat."],
  },
];

describe("ProblemsPanel (F-010)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders all problem types with type, message, severity, and next steps", () => {
    render(<ProblemsPanel problems={SAMPLE_PROBLEMS} />);

    expect(screen.getByText(/unresolved_assumption/i)).toBeInTheDocument();
    expect(screen.getByText(/missing_required_input/i)).toBeInTheDocument();
    expect(screen.getByText(/Blocking question/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirm assumption/i)).toBeInTheDocument();
  });

  it("sorts blocking problems before warnings", () => {
    render(<ProblemsPanel problems={SAMPLE_PROBLEMS} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows[0].textContent).toMatch(/blocking/i);
  });

  it("shows friendly empty state when no problems", () => {
    render(<ProblemsPanel problems={[]} />);
    expect(screen.getByText(/no problems/i)).toBeInTheDocument();
  });

  it("calls onNavigate when a problem with part_id is clicked", () => {
    const onNavigate = vi.fn();
    render(<ProblemsPanel problems={SAMPLE_PROBLEMS} onNavigate={onNavigate} />);

    fireEvent.click(screen.getByText(/High-importance assumption/i));
    expect(onNavigate).toHaveBeenCalledWith(
      expect.objectContaining({ part_id: "mounting_plate" }),
    );
  });

  it("updates when problems prop changes after execute", () => {
    const { rerender } = render(<ProblemsPanel problems={[]} />);
    expect(screen.getByText(/no problems/i)).toBeInTheDocument();

    rerender(<ProblemsPanel problems={SAMPLE_PROBLEMS} />);
    expect(screen.queryByText(/no problems/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Blocking question/i)).toBeInTheDocument();
  });
});
