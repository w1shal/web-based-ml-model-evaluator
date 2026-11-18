import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ConfigurePage from "../pages/ConfigurePage";
import EvaluatePage from "../pages/EvaluatePage";
import UploadPage from "../pages/UploadPage";
import type { UploadedDataset, EvaluationConfig } from "../types/workflow";

const dataset: UploadedDataset = {
  dataset_id: "ds_test123",
  name: "sample.csv",
  columns: ["age", "income", "class"],
  preview: [{ age: 21, income: 30000, class: "A" }],
  warnings: [],
};

const config: EvaluationConfig = {
  dataset_id: "ds_test123",
  target_column: "class",
  feature_columns: ["age", "income"],
  algorithms: ["logistic_regression"],
  test_size: 0.2,
  missing_value_strategy: "median_imputation",
};

describe("workflow pages", () => {
  it("renders the upload page and CSV picker", () => {
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    expect(screen.getByRole("heading", { name: "Upload your dataset" })).toBeInTheDocument();
    expect(screen.getByLabelText("Choose CSV dataset")).toBeInTheDocument();
  });

  it("renders dataset information and configuration controls", () => {
    render(<ConfigurePage dataset={dataset} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    expect(screen.getByRole("heading", { name: "Configure your evaluation" })).toBeInTheDocument();
    expect(screen.getByLabelText("Target column")).toHaveValue("class");
    expect(screen.getByRole("checkbox", { name: /age/i })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /class/i })).toBeDisabled();
  });

  it("asks for a dataset when configuration is opened without one", () => {
    render(<ConfigurePage dataset={null} onConfigChange={() => {}} onContinue={() => {}} onBack={() => {}} />);
    expect(screen.getByText(/Upload a dataset before choosing/)).toBeInTheDocument();
  });

  it("shows the validated configuration before evaluation", () => {
    render(<EvaluatePage config={config} onEvaluationComplete={() => {}} onEditConfiguration={() => {}} />);
    expect(screen.getByRole("heading", { name: "Ready to evaluate" })).toBeInTheDocument();
    expect(screen.getByText("Logistic Regression")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run evaluation/ })).toBeEnabled();
  });

  it("prevents evaluation without a configuration", () => {
    render(<EvaluatePage config={null} onEvaluationComplete={() => {}} onEditConfiguration={() => {}} />);
    expect(screen.getByText(/No valid configuration is available/)).toBeInTheDocument();
  });
});
