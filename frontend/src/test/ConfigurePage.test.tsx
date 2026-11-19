import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConfigurePage from "../pages/ConfigurePage";
import type { UploadedDataset } from "../types/workflow";

const dataset: UploadedDataset = {
  dataset_id: "ds_config123",
  name: "students.csv",
  columns: ["age", "score", "class"],
  preview: [],
  warnings: [],
};

describe("ConfigurePage", () => {
  it("chooses the last column as the default target and excludes it from input features", () => {
    render(<ConfigurePage dataset={dataset} onConfigChange={vi.fn()} onContinue={vi.fn()} onBack={vi.fn()} />);
    expect(screen.getByLabelText("Target column")).toHaveValue("class");
    expect(screen.getByRole("checkbox", { name: /class/i })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: /age/i })).toBeChecked();
  });

  it("validates the config and sends the normalized backend contract", async () => {
    const user = userEvent.setup();
    const onConfigChange = vi.fn();
    const onContinue = vi.fn();
    render(<ConfigurePage dataset={dataset} onConfigChange={onConfigChange} onContinue={onContinue} onBack={() => {}} />);

    await user.click(screen.getByRole("checkbox", { name: /Random Forest/i }));
    await user.click(screen.getByRole("button", { name: "Validate configuration" }));

    expect(onConfigChange).toHaveBeenLastCalledWith({
      dataset_id: "ds_config123",
      target_column: "class",
      feature_columns: ["age", "score"],
      algorithms: ["logistic_regression", "random_forest"],
      test_size: 0.2,
      missing_value_strategy: "median_imputation",
    });
    expect(screen.getByRole("status")).toHaveTextContent("Configuration validated");
    await user.click(screen.getByRole("button", { name: /Continue to evaluation/ }));
    expect(onContinue).toHaveBeenCalledOnce();
  });

  it("rejects a configuration with no input features", async () => {
    const user = userEvent.setup();
    const onConfigChange = vi.fn();
    render(<ConfigurePage dataset={dataset} onConfigChange={onConfigChange} onContinue={() => {}} onBack={() => {}} />);
    await user.click(screen.getByRole("checkbox", { name: /age/i }));
    await user.click(screen.getByRole("checkbox", { name: /score/i }));
    await user.click(screen.getByRole("button", { name: "Validate configuration" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Select at least one feature column");
    expect(onConfigChange).toHaveBeenLastCalledWith(null);
  });

  it("rejects a configuration with no algorithms", async () => {
    const user = userEvent.setup();
    render(<ConfigurePage dataset={dataset} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    await user.click(screen.getByRole("checkbox", { name: /Logistic Regression/i }));
    await user.click(screen.getByRole("button", { name: "Validate configuration" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Select at least one algorithm");
  });

  it("updates the target column and keeps it disabled as an input", async () => {
    const user = userEvent.setup();
    render(<ConfigurePage dataset={dataset} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    await user.selectOptions(screen.getByLabelText("Target column"), "age");
    expect(screen.getByRole("checkbox", { name: /age/i })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: /class/i })).not.toBeChecked();
  });

  it("updates train/test split and missing-value strategy", async () => {
    const user = userEvent.setup();
    render(<ConfigurePage dataset={dataset} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    fireEvent.change(screen.getByLabelText("Test data"), { target: { value: "30" } });
    expect(screen.getByText("Training: 70%")).toBeInTheDocument();
    expect(screen.getByText("Testing: 30%")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Strategy"), "drop_rows");
    await user.click(screen.getByRole("button", { name: "Validate configuration" }));
    expect(screen.getByRole("status")).toHaveTextContent("Configuration validated");
  });

  it("provides a safe back action", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<ConfigurePage dataset={dataset} onConfigChange={() => {}} onContinue={() => {}} onBack={onBack} />);
    await user.click(screen.getByRole("button", { name: "Back to upload" }));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("asks for an upload when no dataset is provided", () => {
    render(<ConfigurePage dataset={null} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    expect(screen.getByText(/Upload a dataset before choosing/)).toBeInTheDocument();
  });
});
