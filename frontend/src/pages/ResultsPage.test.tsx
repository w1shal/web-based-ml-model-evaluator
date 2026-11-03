import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ResultsPage from "./ResultsPage";
import type { EvaluationResponse } from "../types/workflow";

const mockResults: EvaluationResponse = {
  run_id: "run_001",
  status: "completed",
  results: [
    {
      algorithm: "random_forest",
      accuracy: 0.92,
      precision: 0.91,
      recall: 0.90,
      f1_score: 0.905,
    },
    {
      algorithm: "logistic_regression",
      accuracy: 0.88,
      precision: 0.87,
      recall: 0.86,
      f1_score: 0.865,
    },
  ],
};

describe("ResultsPage", () => {
  it("displays results for multiple algorithms", () => {
    render(<ResultsPage data={mockResults} />);

    expect(screen.getByText("random forest")).toBeInTheDocument();
    expect(screen.getByText("logistic regression")).toBeInTheDocument();
    expect(screen.getByText("2 models evaluated")).toBeInTheDocument();
  });

  it("formats metrics as percentages", () => {
    render(<ResultsPage data={mockResults} />);

    expect(screen.getByText("92.00%")).toBeInTheDocument();
    expect(screen.getByText("91.00%")).toBeInTheDocument();
    expect(screen.getByText("90.00%")).toBeInTheDocument();
    expect(screen.getByText("90.50%")).toBeInTheDocument();
  });

  it("displays an empty state when results are unavailable", () => {
    render(
      <ResultsPage
        data={{
          run_id: "run_002",
          status: "completed",
          results: [],
        }}
      />,
    );

    expect(
      screen.getByText("No evaluation results available"),
    ).toBeInTheDocument();
  });

  it("displays an empty state when response is null", () => {
    render(<ResultsPage data={null} />);

    expect(
      screen.getByText("No evaluation results available"),
    ).toBeInTheDocument();
  });

  it("displays a loading state", () => {
    render(<ResultsPage data={null} loading />);

    expect(
      screen.getByText("Loading evaluation results..."),
    ).toBeInTheDocument();
  });

  it("displays an API error", () => {
    render(
      <ResultsPage
        data={null}
        error="Unable to reach the backend."
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Unable to reach the backend.",
    );
  });

  it("displays missing metrics as N/A", () => {
    const incompleteResults = {
      run_id: "run_003",
      status: "completed",
      results: [
        {
          algorithm: "decision_tree",
          accuracy: null,
          precision: 0.85,
          recall: 0.80,
          f1_score: 0.82,
        },
      ],
    };

    render(<ResultsPage data={incompleteResults} />);

    expect(screen.getByText("N/A")).toBeInTheDocument();
    expect(screen.getByText("85.00%")).toBeInTheDocument();
  });
});