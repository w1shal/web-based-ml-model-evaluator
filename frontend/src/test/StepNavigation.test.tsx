import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StepNavigation from "../components/StepNavigation";
import { WORKFLOW_STEPS } from "../types/workflow";

describe("StepNavigation", () => {
  it("renders every workflow step in order", () => {
    render(<StepNavigation currentStep="upload" onStepChange={() => {}} />);

    const nav = screen.getByRole("navigation", { name: "Evaluation workflow" });
    const buttons = nav.querySelectorAll("button");
    expect(buttons).toHaveLength(WORKFLOW_STEPS.length);
    expect([...buttons].map((button) => button.querySelector(".step-title")?.textContent)).toEqual([
      "Upload",
      "Configure",
      "Evaluate",
      "Results",
    ]);
  });

  it("marks the current step and completes earlier ones", () => {
    render(<StepNavigation currentStep="evaluate" onStepChange={() => {}} />);

    const upload = screen.getByRole("button", { name: /upload/i });
    const configure = screen.getByRole("button", { name: /configure/i });
    const evaluate = screen.getByRole("button", { name: /evaluate/i });
    const results = screen.getByRole("button", { name: /results/i });

    expect(evaluate).toHaveAttribute("aria-current", "step");
    expect(evaluate).toHaveClass("workflow-step", "active");
    expect(upload).not.toHaveAttribute("aria-current");

    for (const done of [upload, configure]) {
      expect(done).toHaveClass("complete");
      expect(done.querySelector(".step-number")).toHaveTextContent("✓");
    }
    expect(evaluate.querySelector(".step-number")).toHaveTextContent("3");
    expect(results).not.toHaveClass("complete");
    expect(results).not.toHaveClass("active");
    expect(results.querySelector(".step-number")).toHaveTextContent("4");
  });

  it("calls onStepChange with the clicked step id", async () => {
    const user = userEvent.setup();
    const onStepChange = vi.fn();
    render(<StepNavigation currentStep="upload" onStepChange={onStepChange} />);

    await user.click(screen.getByRole("button", { name: /results/i }));
    await user.click(screen.getByRole("button", { name: /configure/i }));

    expect(onStepChange.mock.calls).toEqual([["results"], ["configure"]]);
  });
});
