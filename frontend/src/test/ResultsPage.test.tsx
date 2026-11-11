import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResultsPage from "../pages/ResultsPage";
import { api } from "../lib/api";
import type { EvaluationRunDetail } from "../types/results";

vi.mock("../lib/api", () => ({
  api: {
    downloadReport: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

const run: EvaluationRunDetail = {
  run_id: "run_abc123",
  dataset_name: "Iris.csv",
  timestamp: "2026-11-10T12:00:00Z",
  status: "completed",
  algorithms: ["Random Forest", "Decision Tree", "Logistic Regression"],
  metrics: [
    {
      algorithm: "Random Forest",
      accuracy: 0.92,
      precision: 0.91,
      recall: 0.9,
      f1_score: 0.905,
      roc_auc: 0.95,
      class_labels: ["setosa", "versicolor", "virginica"],
    },
    {
      algorithm: "Decision Tree",
      accuracy: 0.92,
      precision: 0.9,
      recall: 0.89,
      f1_score: 0.895,
      roc_auc: null,
      class_labels: ["setosa", "versicolor", "virginica"],
    },
    {
      algorithm: "Logistic Regression",
      accuracy: 0.88,
      precision: 0.87,
      recall: 0.86,
      f1_score: 0.865,
      roc_auc: 0.93,
      class_labels: ["setosa", "versicolor", "virginica"],
    },
  ],
  target_column: "species",
  feature_columns: ["sepal_length", "petal_length"],
  split_ratio: 0.2,
  confusion_matrices: {
    "Random Forest": [[45, 5, 0], [4, 43, 3], [0, 2, 48]],
    "Decision Tree": [[44, 6, 0], [5, 41, 4], [0, 3, 47]],
    "Logistic Regression": [[42, 8, 0], [6, 40, 4], [0, 3, 47]],
  },
  confusion_matrix_labels: {
    "Random Forest": ["setosa", "versicolor", "virginica"],
    "Decision Tree": ["setosa", "versicolor", "virginica"],
    "Logistic Regression": ["setosa", "versicolor", "virginica"],
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Evaluation results", () => {
  it("shows metric comparisons and correctly labelled confusion matrix values", () => {
    render(<ResultsPage run={run} />);

    const table = screen.getByRole("table", { name: /model comparison/i });
    const rows = within(table).getAllByRole("row");
    expect(rows.slice(1).map((row) => (row as HTMLTableRowElement).cells[0].textContent)).toEqual([
      "Decision Tree",
      "Random Forest",
      "Logistic Regression",
    ]);
    expect(within(table).getAllByText("92.00%")).toHaveLength(2);
    expect(within(table).getByText("N/A (multiclass)")).toBeInTheDocument();

    const matrix = screen.getByRole("table", { name: /random forest confusion matrix/i });
    expect(within(matrix).getAllByText("setosa")).toHaveLength(2);
    expect(
      within(matrix).getByRole("cell", { name: "setosa predicted as setosa: 45" }),
    ).toHaveTextContent("45");

    const chart = screen.getByRole("list", { name: /accuracy comparison/i });
    expect(within(chart).getAllByText("92.00%")).toHaveLength(2);
    expect(within(chart).getByText("88.00%")).toBeInTheDocument();
  });

  it("sorts ascending and keeps ties deterministic", async () => {
    const user = userEvent.setup();
    render(<ResultsPage run={run} />);

    await user.click(screen.getByRole("button", { name: "Sort ascending" }));
    const table = screen.getByRole("table", { name: /model comparison/i });
    const rows = within(table).getAllByRole("row");
    expect(rows.slice(1).map((row) => (row as HTMLTableRowElement).cells[0].textContent)).toEqual([
      "Logistic Regression",
      "Decision Tree",
      "Random Forest",
    ]);
  });

  it("shows a loading state and handles missing matrix data", () => {
    const { rerender } = render(<ResultsPage run={run} loading />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading evaluation results");

    const withoutMatrices = {
      ...run,
      confusion_matrices: {},
    };
    rerender(<ResultsPage run={withoutMatrices} />);
    expect(screen.getByText(/Confusion matrix data is unavailable/)).toBeInTheDocument();
  });

  it("downloads the selected report for the current run", async () => {
    const user = userEvent.setup();
    mockedApi.downloadReport.mockResolvedValue(new Blob(["report"]));
    const createObjectURL = vi.fn(() => "blob:test-report");
    const revokeObjectURL = vi.fn();
    const clickLink = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectURL });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectURL });
    render(<ResultsPage run={run} token="access-token" />);

    await user.click(screen.getByRole("button", { name: "Download CSV" }));

    expect(mockedApi.downloadReport).toHaveBeenCalledWith("run_abc123", "csv", "access-token");
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(clickLink).toHaveBeenCalledOnce();
  });
});
