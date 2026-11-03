import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "../api/client";
import UploadPage from "./UploadPage";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../api/client")>();

  return {
    ...actual,
    apiRequest: apiRequestMock,
  };
});

const successfulResponse = {
  dataset_id: "dataset-123",
  columns: ["Name", "Age", "Score"],
  preview: [
    { Name: "Alice", Age: 22, Score: 90 },
    { Name: "Bob", Age: 24, Score: 85 },
  ],
  warnings: [],
};

describe("UploadPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uploads a CSV and displays the dataset preview", async () => {
    const user = userEvent.setup();
    apiRequestMock.mockResolvedValue(successfulResponse);

    render(<UploadPage onUploadSuccess={() => {}} />);

    const file = new File(
      ["Name,Age,Score\nAlice,22,90"],
      "students.csv",
      { type: "text/csv" },
    );

    await user.upload(screen.getByLabelText(/dataset-file/i), file);

    await user.click(
      screen.getByRole("button", { name: /upload and preview/i }),
    );

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledTimes(1);
    });

    const [endpoint, options] = apiRequestMock.mock.calls[0];

    expect(endpoint).toBe("/datasets/upload");
    expect(options.method).toBe("POST");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("file")).toBe(file);

    expect(await screen.findByText("dataset-123")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Dataset preview")).toBeInTheDocument();
  });

  it("rejects files that are not CSV files", async () => {

    render(<UploadPage onUploadSuccess={() => {}} />);

    const file = new File(["hello"], "notes.txt", {
      type: "text/plain",
    });

    fireEvent.change(screen.getByLabelText(/dataset-file/i), {
  target: { files: [file] },
});

    expect(
      screen.getByText(/unsupported file type/i),
    ).toBeInTheDocument();

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("rejects files larger than 10 MB", async () => {
    const user = userEvent.setup();

    render(<UploadPage onUploadSuccess={() => {}} />);

    const file = new File(
      [new Uint8Array(10 * 1024 * 1024 + 1)],
      "large.csv",
      { type: "text/csv" },
    );

    await user.upload(screen.getByLabelText(/dataset-file/i), file);

    expect(
      screen.getByText(/exceeds 10 MB/i),
    ).toBeInTheDocument();

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("displays a backend error when CSV parsing fails", async () => {
    const user = userEvent.setup();

    apiRequestMock.mockRejectedValue(
      new ApiError("Malformed CSV file", 400),
    );

    render(<UploadPage onUploadSuccess={() => {}} />);

    const file = new File(["invalid,csv"], "broken.csv", {
      type: "text/csv",
    });

    await user.upload(screen.getByLabelText(/dataset-file/i), file);

    await user.click(
      screen.getByRole("button", { name: /upload and preview/i }),
    );

    expect(
      await screen.findByText("Malformed CSV file"),
    ).toBeInTheDocument();

    expect(apiRequestMock).toHaveBeenCalledTimes(1);
  });

  it("prevents repeated submissions while uploading", async () => {
    const user = userEvent.setup();

    let resolveUpload!: (value: typeof successfulResponse) => void;

    apiRequestMock.mockReturnValue(
      new Promise((resolve) => {
        resolveUpload = resolve;
      }),
    );

    render(<UploadPage onUploadSuccess={() => {}} />);

    const file = new File(["Name\nAlice"], "students.csv", {
      type: "text/csv",
    });

    await user.upload(screen.getByLabelText(/dataset-file/i), file);

    const uploadButton = screen.getByRole("button", {
      name: /upload and preview/i,
    });

    await user.click(uploadButton);

    expect(
      await screen.findByRole("status"),
    ).toBeInTheDocument();

    expect(uploadButton).toBeDisabled();

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledTimes(1);
    });

    resolveUpload(successfulResponse);

    expect(await screen.findByText("dataset-123")).toBeInTheDocument();
  });

  it("allows retrying with another file after an error", async () => {
    const user = userEvent.setup();

    apiRequestMock
      .mockRejectedValueOnce(new ApiError("Server error", 500))
      .mockResolvedValueOnce(successfulResponse);

    render(<UploadPage onUploadSuccess={() => {}} />);

    const input = screen.getByLabelText(/dataset-file/i);

    const firstFile = new File(["bad"], "first.csv", {
      type: "text/csv",
    });

    await user.upload(input, firstFile);

    await user.click(
      screen.getByRole("button", { name: /upload and preview/i }),
    );

    expect(await screen.findByText("Server error")).toBeInTheDocument();

    const secondFile = new File(["good"], "second.csv", {
      type: "text/csv",
    });

    await user.upload(input, secondFile);

    await user.click(
      screen.getByRole("button", { name: /upload and preview/i }),
    );

    expect(await screen.findByText("dataset-123")).toBeInTheDocument();

    expect(apiRequestMock).toHaveBeenCalledTimes(2);
  });
});