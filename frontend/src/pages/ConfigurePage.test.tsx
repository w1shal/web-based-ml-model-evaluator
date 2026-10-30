import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConfigurePage from "./ConfigurePage";
import type { UploadedDataset } from "../types/workflow";

const mockDataset: UploadedDataset = {
  dataset_id: "dataset-123",
  columns: ["Name", "Age", "Score"],
  preview: [],
  warnings: [],
};

describe("ConfigurePage", () => {
  it("displays uploaded dataset columns", () => {
    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={vi.fn()}
      />,
    );

    expect(screen.getByText(/dataset-123/)).toBeInTheDocument();
    expect(screen.getByText("Available columns: 3")).toBeInTheDocument();
  });

  it("prevents the target column from being selected as a feature", () => {
    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={vi.fn()}
      />,
    );

    const targetCheckbox = screen.getByRole("checkbox", {
      name: /Name/,
    });

    expect(targetCheckbox).toBeDisabled();
  });

  it("allows selecting and deselecting feature columns", async () => {
    const user = userEvent.setup();

    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={vi.fn()}
      />,
    );

    const ageCheckbox = screen.getByRole("checkbox", {
      name: "Age",
    });

    expect(ageCheckbox).toBeChecked();

    await user.click(ageCheckbox);

    expect(ageCheckbox).not.toBeChecked();
  });

  it("allows selecting multiple algorithms", async () => {
    const user = userEvent.setup();

    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={vi.fn()}
      />,
    );

    const decisionTree = screen.getByRole("checkbox", {
      name: "Decision Tree",
    });

    await user.click(decisionTree);

    expect(decisionTree).toBeChecked();
    expect(
      screen.getByText("2 of 5 algorithms selected"),
    ).toBeInTheDocument();
  });

  it("updates the train/test split", () => {
    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={vi.fn()}
      />,
    );

    const slider = screen.getByRole("slider");

    fireEvent.change(slider, {
      target: { value: "30" },
    });

    expect(screen.getByText("Training: 70%")).toBeInTheDocument();
    expect(screen.getByText("Testing: 30%")).toBeInTheDocument();
  });

  it("rejects configuration without feature columns", async () => {
    const user = userEvent.setup();
    const onConfigChange = vi.fn();

    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={onConfigChange}
      />,
    );

    await user.click(
      screen.getByRole("checkbox", { name: "Age" }),
    );

    await user.click(
      screen.getByRole("checkbox", { name: "Score" }),
    );

    await user.click(
      screen.getByRole("button", {
        name: /validate configuration/i,
      }),
    );

    expect(
      screen.getByText("Please select at least one feature column."),
    ).toBeInTheDocument();

    expect(onConfigChange).toHaveBeenLastCalledWith(null);
  });

  it("sends the correct configuration when validated", async () => {
    const user = userEvent.setup();
    const onConfigChange = vi.fn();

    render(
      <ConfigurePage
        dataset={mockDataset}
        onConfigChange={onConfigChange}
      />,
    );

    await user.click(
      screen.getByRole("checkbox", {
        name: "Decision Tree",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: /validate configuration/i,
      }),
    );

    expect(onConfigChange).toHaveBeenLastCalledWith({
      dataset_id: "dataset-123",
      target_column: "Name",
      feature_columns: ["Age", "Score"],
      algorithms: ["logistic_regression", "decision_tree"],
      test_size: 0.2,
      missing_value_strategy: "median_imputation",
    });
  });
});