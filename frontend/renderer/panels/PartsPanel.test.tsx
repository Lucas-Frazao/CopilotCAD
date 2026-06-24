import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import PartsPanel from "./PartsPanel";

const SAMPLE_PARTS = [
  {
    part_id: "mounting_plate",
    name: "Mounting Plate",
    maturity: "draft",
    open_problem_count: 2,
  },
  {
    part_id: "bracket",
    name: "Bracket",
    maturity: "in_review",
    open_problem_count: 0,
  },
];

describe("PartsPanel (F-015)", () => {
  afterEach(() => {
    cleanup();
  });

  it("lists all parts with maturity badge and problem count", () => {
    render(<PartsPanel parts={SAMPLE_PARTS} activePartId={null} />);

    expect(screen.getByText(/mounting_plate|Mounting Plate/i)).toBeInTheDocument();
    expect(screen.getByText(/draft/i)).toBeInTheDocument();
    expect(screen.getByText(/2/)).toBeInTheDocument();
    expect(screen.getByText(/in_review|in review/i)).toBeInTheDocument();
  });

  it("selecting a part calls onSelectPart", () => {
    const onSelect = vi.fn();
    render(
      <PartsPanel
        parts={SAMPLE_PARTS}
        activePartId={null}
        onSelectPart={onSelect}
      />,
    );

    fireEvent.click(screen.getByText(/Mounting Plate/i));
    expect(onSelect).toHaveBeenCalledWith("mounting_plate");
  });

  it("highlights active part", () => {
    render(<PartsPanel parts={SAMPLE_PARTS} activePartId="mounting_plate" />);
    const row = screen.getByRole("button", { name: /Mounting Plate/i });
    expect(row).toHaveAttribute("aria-selected", "true");
  });

  it("shows empty state when no parts exist", () => {
    render(<PartsPanel parts={[]} activePartId={null} />);
    expect(screen.getByText(/no parts yet/i)).toBeInTheDocument();
    expect(screen.getByText(/\/part|chat/i)).toBeInTheDocument();
  });
});
