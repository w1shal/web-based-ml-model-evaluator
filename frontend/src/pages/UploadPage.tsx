import { useRef, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import type { UploadedDataset } from "../types/workflow";

const MAX_FILE_SIZE = 10 * 1024 * 1024;


function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 400 || error.status === 422) {
      return error.message || "The CSV file could not be parsed. Check its contents and try again.";
    }

    if (error.status === 413) {
      return "This file is larger than the 10 MB upload limit.";
    }

    if (error.status === 415) {
      return "Unsupported file type. Please select a CSV file.";
    }

    return error.message;
  }

  return "Something went wrong while uploading. Please try again.";
}

interface UploadPageProps {
  onUploadSuccess: (dataset: UploadedDataset) => void;
}

export default function UploadPage({ onUploadSuccess }: UploadPageProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadedDataset | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(file: File | null) {
    setError("");
    setResult(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setSelectedFile(null);
      setError("Unsupported file type. Please select a .csv file.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);
      setError("File size exceeds 10 MB. Please choose a smaller CSV file.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    if (file.size === 0) {
      setSelectedFile(null);
      setError("The selected file is empty. Please choose a valid CSV file.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await apiRequest<UploadedDataset>(
        "/datasets/upload",
        {
          method: "POST",
          body: formData,
        },
      );

      if (
        !response ||
        !Array.isArray(response.columns) ||
        !Array.isArray(response.preview)
      ) {
        throw new Error("The backend returned an invalid upload response.");
      }

      setResult(response);
      onUploadSuccess(response);
    } catch (uploadError) {
      setError(getErrorMessage(uploadError));
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="page-content upload-page">
      <span className="eyebrow">STEP 01</span>
      <h2>Upload your dataset</h2>
      <p>
        Select a CSV dataset to begin your machine learning evaluation.
        We will inspect its columns and show a preview before you continue.
      </p>

      <div className="upload-panel">
        <div className="upload-icon" aria-hidden="true">
          ↑
        </div>

        <h3>Choose your CSV file</h3>
        <p>Upload a comma-separated values file to get started.</p>

        <label
  className="file-picker-button"
  htmlFor="dataset-file"
>
  Browse files
</label>
<span id="dataset-file-description" className="upload-hint">
  CSV format only · Maximum file size: 10 MB
</span>

        <input
          ref={fileInputRef}
          id="dataset-file"
          aria-label="dataset-file"
          aria-describedby="dataset-file-description"
          className="file-input"
          type="file"
          accept=".csv,text/csv"
          disabled={uploading}
          onChange={(event) =>
            handleFileChange(event.target.files?.[0] ?? null)
          }
        />

        <span className="upload-hint">
          CSV format only · Maximum file size: 10 MB
        </span>

        {selectedFile && (
          <div className="selected-file">
            <span aria-hidden="true">▤</span>
            <div>
              <strong>{selectedFile.name}</strong>
              <small>{(selectedFile.size / 1024).toFixed(1)} KB</small>
            </div>
            <button
              type="button"
              className="remove-file-button"
              disabled={uploading}
              onClick={() => {
                setSelectedFile(null);
                setResult(null);
                setError("");
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              aria-label="Remove selected file"
            >
              ×
            </button>
          </div>
        )}

        {error && (
          <div className="upload-error" role="alert">
            <strong>Upload failed</strong>
            <span>{error}</span>
          </div>
        )}

        <button
          type="button"
          className="button-primary upload-submit"
          disabled={!selectedFile || uploading}
          onClick={handleUpload}
        >
          {uploading ? "Uploading..." : "Upload and preview"}
        </button>

        {uploading && (
          <p className="upload-loading" role="status">
            Uploading and processing your dataset. Please wait...
          </p>
        )}
      </div>

      {result && (
        <div className="preview-section" aria-live="polite">
          <div className="preview-heading">
            <div>
              <span className="eyebrow">UPLOAD SUCCESSFUL</span>
              <h3>Dataset preview</h3>
            </div>
            <span className="success-label">Ready</span>
          </div>

          <div className="dataset-summary">
            <div>
              <small>Dataset ID</small>
              <strong>{result.dataset_id}</strong>
            </div>
            <div>
              <small>Columns</small>
              <strong>{result.columns.length}</strong>
            </div>
            <div>
              <small>Preview rows</small>
              <strong>{result.preview.length}</strong>
            </div>
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div className="upload-warning">
              <strong>Warnings</strong>
              <ul>
                {result.warnings.map((warning, index) => (
                  <li key={`${index}-${warning}`}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="preview-table-wrapper">
            <table className="preview-table">
              <thead>
                <tr>
                  {result.columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.preview.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {result.columns.map((column, columnIndex) => {
                      const value = Array.isArray(row)
                        ? row[columnIndex]
                        : row[column];

                      return <td key={column}>{formatCell(value)}</td>;
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {result.preview.length === 0 && (
            <p className="empty-preview">
              The upload succeeded, but the backend returned no preview rows.
            </p>
          )}
        </div>
      )}
    </section>
  );
}