import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HistoryPage from "../pages/HistoryPage";

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiRequest: apiRequestMock };
});

const rows = {
  items: [{
    run_id: "run_history123",
    dataset_name: "customers.csv",
    timestamp: "2026-11-18T10:00:00Z",
    status: "completed",
    algorithms: ["random_forest"],
    metrics: [{
      algorithm: "random_forest",
      accuracy: 0.91,
      precision: 0.9,
      recall: 0.92,
      f1_score: 0.91,
      roc_auc: 0.94,
    }],
  }],
  total: 1,
  limit: 50,
  offset: 0,
};

describe("HistoryPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("loads the current user's history and opens a selected run", async () => {
    const user = userEvent.setup();
    const onOpen = vi.fn();
    apiRequestMock.mockResolvedValue(rows);

    render(<HistoryPage token="user-token" onOpen={onOpen} onClose={() => {}} />);

    expect(await screen.findByRole("heading", { name: "customers.csv" })).toBeInTheDocument();
    expect(screen.getByText("91.0%")).toBeInTheDocument();
    expect(apiRequestMock).toHaveBeenCalledWith("/history?limit=50&offset=0", { token: "user-token" });

    await user.click(screen.getByRole("button", { name: "View results" }));
    expect(onOpen).toHaveBeenCalledWith("run_history123");
  });

  it("shows an empty state when no saved runs exist", async () => {
    apiRequestMock.mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    render(<HistoryPage token="user-token" onOpen={() => {}} onClose={() => {}} />);
    expect(await screen.findByRole("heading", { name: "No saved evaluations yet" })).toBeInTheDocument();
  });

  it("shows a backend error when history cannot be loaded", async () => {
    apiRequestMock.mockRejectedValue(new Error("Authentication required"));
    render(<HistoryPage token="expired-token" onOpen={() => {}} onClose={() => {}} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Authentication required");
  });

  it("refreshes the list and calls close", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    apiRequestMock.mockResolvedValue(rows);
    render(<HistoryPage token="user-token" onOpen={() => {}} onClose={onClose} />);
    await screen.findByRole("heading", { name: "customers.csv" });
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(apiRequestMock).toHaveBeenCalledTimes(2));
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("requires confirmation before deleting and then refreshes history", async () => {
    const user = userEvent.setup();
    apiRequestMock
      .mockResolvedValueOnce(rows)
      .mockResolvedValueOnce({ message: "Run deleted" })
      .mockResolvedValueOnce({ items: [], total: 0, limit: 50, offset: 0 });

    render(<HistoryPage token="user-token" onOpen={() => {}} onClose={() => {}} />);
    await screen.findByRole("heading", { name: "customers.csv" });

    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.getByText("Delete this run?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText("Delete this run?")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm delete" }));

    expect(await screen.findByRole("heading", { name: "No saved evaluations yet" })).toBeInTheDocument();
    expect(apiRequestMock).toHaveBeenCalledWith("/history/run_history123", {
      method: "DELETE",
      token: "user-token",
    });
  });

  it("shows an error if deleting a history entry is rejected", async () => {
    const user = userEvent.setup();
    apiRequestMock
      .mockResolvedValueOnce(rows)
      .mockRejectedValueOnce(new Error("You do not have access to this run"));

    render(<HistoryPage token="user-token" onOpen={() => {}} onClose={() => {}} />);
    await screen.findByRole("heading", { name: "customers.csv" });
    await user.click(screen.getByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm delete" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("You do not have access to this run");
  });
});
