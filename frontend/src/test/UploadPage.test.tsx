import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "../api/client";
import UploadPage from "../pages/UploadPage";
import type { UploadedDataset } from "../types/workflow";

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiRequest: apiRequestMock };
});

const result: UploadedDataset = {
  dataset_id: "ds_upload123",
  name: "students.csv",
  columns: ["age", "score", "class"],
  preview: [
    { age: 21, score: 89, class: "A" },
    { age: 23, score: 92, class: "B" },
  ],
  warnings: ["Column 'score' contains 1 missing value(s)."],
};

describe("UploadPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("uploads a CSV, shows its preview and lets the user continue", async () => {
    const user = userEvent.setup();
    const onUploadSuccess = vi.fn();
    const onContinue = vi.fn();
    apiRequestMock.mockResolvedValue(result);
    render(<UploadPage token="upload-token" onUploadSuccess={onUploadSuccess} onContinue={onContinue} />);

    const file = new File(["age,score,class\n21,89,A"], "students.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText("Choose CSV dataset"), file);
    await user.click(screen.getByRole("button", { name: "Upload and preview" }));

    expect(await screen.findByText("ds_upload123")).toBeInTheDocument();
    expect(screen.getByText("students.csv")).toBeInTheDocument();
    expect(screen.getByText("Column 'score' contains 1 missing value(s).")).toBeInTheDocument();
    expect(screen.getByText("21")).toBeInTheDocument();
    expect(onUploadSuccess).toHaveBeenCalledWith({ ...result, name: "students.csv" });

    const [path, options] = apiRequestMock.mock.calls[0];
    expect(path).toBe("/datasets/upload");
    expect(options.method).toBe("POST");
    expect(options.token).toBe("upload-token");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("file")).toBe(file);

    await user.click(screen.getByRole("button", { name: /Continue to configuration/ }));
    expect(onContinue).toHaveBeenCalledOnce();
  });

  it("rejects non-CSV file names before calling the API", async () => {
    const user = userEvent.setup();
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    const file = new File(["text"], "notes.txt", { type: "text/plain" });
    await user.upload(screen.getByLabelText("Choose CSV dataset"), file);
    expect(screen.getByRole("alert")).toHaveTextContent("Unsupported file type");
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("rejects empty and oversized CSV files", async () => {
    const user = userEvent.setup();
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    const input = screen.getByLabelText("Choose CSV dataset");

    await user.upload(input, new File([""], "empty.csv", { type: "text/csv" }));
    expect(screen.getByRole("alert")).toHaveTextContent("selected file is empty");

    await user.upload(input, new File([new Uint8Array(10 * 1024 * 1024 + 1)], "large.csv", { type: "text/csv" }));
    expect(screen.getByRole("alert")).toHaveTextContent("exceeds 10 MB");
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("clears the selected file when the user removes it", async () => {
    const user = userEvent.setup();
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    const input = screen.getByLabelText("Choose CSV dataset");
    await user.upload(input, new File(["a,b\n1,2"], "sample.csv", { type: "text/csv" }));
    expect(screen.getByText("sample.csv")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Remove" }));
    expect(screen.queryByText("sample.csv")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload and preview" })).toBeDisabled();
  });

  it.each([
    [400, "CSV could not be parsed"],
    [413, "larger than the 10 MB upload limit"],
    [415, "Unsupported file type"],
    [500, "Server failed"],
  ])("maps backend upload status %s into a readable error", async (status, message) => {
    const user = userEvent.setup();
    apiRequestMock.mockRejectedValue(new ApiError(status === 400 ? "CSV could not be parsed" : status === 500 ? "Server failed" : "Backend rejected the upload", status));
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);

    await user.upload(screen.getByLabelText("Choose CSV dataset"), new File(["a,b\n1,2"], "sample.csv", { type: "text/csv" }));
    await user.click(screen.getByRole("button", { name: "Upload and preview" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });

  it("allows retry after a backend error", async () => {
    const user = userEvent.setup();
    apiRequestMock.mockRejectedValueOnce(new ApiError("Malformed CSV file", 400)).mockResolvedValueOnce(result);
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    const input = screen.getByLabelText("Choose CSV dataset");

    await user.upload(input, new File(["bad"], "first.csv", { type: "text/csv" }));
    await user.click(screen.getByRole("button", { name: "Upload and preview" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();

    await user.upload(input, new File(["good"], "second.csv", { type: "text/csv" }));
    await user.click(screen.getByRole("button", { name: "Upload and preview" }));
    expect(await screen.findByText("ds_upload123")).toBeInTheDocument();
    expect(apiRequestMock).toHaveBeenCalledTimes(2);
  });

  it("shows a message if the backend returns an invalid payload", async () => {
    const user = userEvent.setup();
    apiRequestMock.mockResolvedValue({ dataset_id: "ds_bad", columns: "not-array", preview: [] });
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    await user.upload(screen.getByLabelText("Choose CSV dataset"), new File(["a,b"], "sample.csv", { type: "text/csv" }));
    await user.click(screen.getByRole("button", { name: "Upload and preview" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("invalid upload response");
  });

  it("handles a cleared file input", () => {
    render(<UploadPage onUploadSuccess={() => {}} onContinue={() => {}} />);
    fireEvent.change(screen.getByLabelText("Choose CSV dataset"), { target: { files: [] } });
    expect(screen.getByRole("button", { name: "Upload and preview" })).toBeDisabled();
  });
});
