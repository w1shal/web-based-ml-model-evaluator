import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { api } from "../lib/api";
import type { AuthUser } from "../lib/api";

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiRequest: apiRequestMock };
});

vi.mock("../lib/api", () => ({
  api: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
    historyEntry: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);
const demoUser: AuthUser = {
  user_id: 7,
  username: "workflow_demo",
  email: "workflow.demo@example.com",
};

const uploadedDataset = {
  dataset_id: "ds_demo123",
  columns: ["age", "income", "label"],
  preview: [{ age: 25, income: 45000, label: "yes" }],
  warnings: [],
};

const evaluationResult = {
  run_id: "run_demo123",
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

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.login.mockResolvedValue({
    access_token: "demo-access-token",
    token_type: "bearer",
    expires_in: 3600,
    user: demoUser,
  });
  mockedApi.historyEntry.mockRejectedValue(new Error("Use immediate evaluation response"));
  apiRequestMock.mockImplementation(async (path: string) => {
    if (path === "/datasets/upload") return uploadedDataset;
    if (path === "/evaluations") return evaluationResult;
    throw new Error("Unexpected API path: " + path);
  });
});

describe("integrated upload-to-results workflow", () => {
  it("uploads a CSV, validates model settings, runs the backend evaluation, and displays results", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("Username or email"), demoUser.email);
    await user.type(screen.getByLabelText("Password"), "DemoPassword123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    const file = new File(["age,income,label\n25,45000,yes"], "customers.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText("Choose CSV dataset"), file);
    await user.click(screen.getByRole("button", { name: /Upload and preview/i }));

    expect(await screen.findByText("ds_demo123")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Continue to configuration/i }));

    expect(screen.getByRole("heading", { name: "Configure your evaluation" })).toBeInTheDocument();
    expect(screen.getByLabelText("Target column")).toHaveValue("label");
    await user.click(screen.getByRole("button", { name: /Validate configuration/i }));
    await user.click(screen.getByRole("button", { name: /Continue to evaluation/i }));

    expect(screen.getByRole("heading", { name: "Ready to evaluate" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Run evaluation/i }));

    expect(await screen.findByRole("heading", { name: "Results for customers.csv" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Model comparison" })).toBeInTheDocument();

    const evaluationCall = apiRequestMock.mock.calls.find((call) => call[0] === "/evaluations");
    expect(evaluationCall).toBeDefined();
    const body = JSON.parse(evaluationCall![1].body as string);
    expect(body).toMatchObject({
      dataset_id: "ds_demo123",
      target_column: "label",
      feature_columns: ["age", "income"],
      algorithms: ["logistic_regression"],
      test_size: 0.2,
      missing_value_strategy: "median_imputation",
    });
    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(2));
  });
});
