import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EvaluatePage from "../pages/EvaluatePage";
import type { EvaluationConfig, EvaluationApiResponse } from "../types/workflow";

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiRequest: apiRequestMock };
});

const config: EvaluationConfig = {
  dataset_id: "ds_123",
  target_column: "label",
  feature_columns: ["age", "income"],
  algorithms: ["random_forest"],
  test_size: 0.2,
  missing_value_strategy: "median_imputation",
};

const response: EvaluationApiResponse = {
  run_id: "run_123",
  status: "completed",
  dataset: { name: "customers.csv", rows: 100, train_rows: 80, test_rows: 20 },
  results: [{
    algorithm: "random_forest",
    name: "Random Forest",
    status: "completed",
    accuracy: 0.95,
    precision: 0.94,
    recall: 0.96,
    f1_score: 0.95,
    roc_auc: 0.97,
    confusion_matrix: [[9, 1], [0, 10]],
    classes: ["no", "yes"],
  }],
};

describe("EvaluatePage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("posts the validated configuration and returns the backend evaluation result", async () => {
    const user = userEvent.setup();
    const onEvaluationComplete = vi.fn();
    apiRequestMock.mockResolvedValue(response);

    render(
      <EvaluatePage
        config={config}
        datasetName="customers.csv"
        token="access-token"
        onEvaluationComplete={onEvaluationComplete}
        onEditConfiguration={() => {}}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Run evaluation/ }));

    await waitFor(() => expect(onEvaluationComplete).toHaveBeenCalledWith(response));
    expect(apiRequestMock).toHaveBeenCalledWith("/evaluations", {
      method: "POST",
      body: JSON.stringify(config),
      token: "access-token",
    });
    expect(onEvaluationComplete).toHaveBeenCalledWith(response);
  });

  it("shows backend validation errors without losing the configuration", async () => {
    const user = userEvent.setup();
    apiRequestMock.mockRejectedValue(new Error("Dataset does not contain enough rows"));

    render(
      <EvaluatePage
        config={config}
        token={null}
        onEvaluationComplete={() => {}}
        onEditConfiguration={() => {}}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Run evaluation/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Dataset does not contain enough rows");
  });

  it("blocks evaluation when no configuration exists", () => {
    render(
      <EvaluatePage
        config={null}
        onEvaluationComplete={() => {}}
        onEditConfiguration={() => {}}
      />,
    );
    expect(screen.getByText(/No valid configuration is available/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Run evaluation/ })).not.toBeInTheDocument();
  });
});
