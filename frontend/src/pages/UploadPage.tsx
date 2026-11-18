import { useRef, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import type { UploadedDataset } from "../types/workflow";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

interface UploadPageProps {
  token?: string | null;
  onUploadSuccess: (dataset: UploadedDataset) => void;
  onContinue: () => void;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 400 || error.status === 422) {
      return error.message || "The CSV file could not be parsed. Check its contents and try again.";
    }
    if (error.status === 413) return "This file is larger than the 10 MB upload limit.";
    if (error.status === 415) return "Unsupported file type. Please select a CSV file.";
    return error.message;
  }
  return error instanceof Error ? error.message : "Something went wrong while uploading. Please try again.";
}

export default function UploadPage({ token, onUploadSuccess, onContinue }: UploadPageProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadedDataset | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function chooseFile(file: File | null) {
    setError("");
    setResult(null);
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setSelectedFile(null);
      setError("Unsupported file type. Please select a .csv file.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);
      setError("File size exceeds 10 MB. Please choose a smaller CSV file.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    if (file.size === 0) {
      setSelectedFile(null);
      setError("The selected file is empty. Please choose a valid CSV file.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    setSelectedFile(file);
  }

  async function upload() {
    if (!selectedFile || uploading) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const body = new FormData();
      body.append("file", selectedFile);
      const response = await apiRequest<UploadedDataset>("/datasets/upload", {
        method: "POST",
        body,
        token,
      });
      if (!response || !Array.isArray(response.columns) || !Array.isArray(response.preview) || !response.dataset_id) {
        throw new Error("The backend returned an invalid upload response.");
      }
      const uploaded = { ...response, name: selectedFile.name };
      setResult(uploaded);
      onUploadSuccess(uploaded);
    } catch (uploadError) {
      setError(errorMessage(uploadError));
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="workflow-page">
      <div className="workflow-page-heading">
        <span className="eyebrow">STEP 01 · DATASET</span>
        <h2>Upload your dataset</h2>
        <p>Select a CSV classification dataset. The backend will parse it, save it, and return a preview before you configure your experiment.</p>
      </div>

      <div className="upload-panel">
        <div className="upload-icon" aria-hidden="true">↑</div>
        <h3>Choose your CSV file</h3>
        <p>CSV format only · Maximum file size: 10 MB</p>
        <label className="file-picker-button" htmlFor="dataset-file">Browse files</label>
        <input
          ref={inputRef}
          id="dataset-file"
          className="workflow-file-input"
          type="file"
          accept=".csv,text/csv"
          aria-label="Choose CSV dataset"
          disabled={uploading}
          onChange={(event) => chooseFile(event.currentTarget.files?.[0] ?? null)}
        />

        {selectedFile && (
          <div className="selected-file">
            <span aria-hidden="true">▤</span>
            <div className="selected-file-info">
              <strong>{selectedFile.name}</strong>
              <small>{(selectedFile.size / 1024).toFixed(1)} KB</small>
            </div>
            <button
              type="button"
              className="text-button"
              disabled={uploading}
              onClick={() => {
                setSelectedFile(null);
                setResult(null);
                setError("");
                if (inputRef.current) inputRef.current.value = "";
              }}
            >Remove</button>
          </div>
        )}

        {error && <div className="workflow-alert error" role="alert"><strong>Upload failed</strong><span>{error}</span></div>}

        <button type="button" className="button button-primary workflow-submit" disabled={!selectedFile || uploading} onClick={() => void upload()}>
          {uploading ? "Uploading and processing…" : "Upload and preview"}
        </button>
        {uploading && <p className="workflow-status" role="status">Uploading the dataset and preparing its preview…</p>}
      </div>

      {result && (
        <section className="dataset-preview-card" aria-live="polite">
          <div className="preview-heading">
            <div>
              <span className="eyebrow">UPLOAD SUCCESSFUL</span>
              <h3>{result.name || "Dataset preview"}</h3>
            </div>
            <span className="success-label">Saved</span>
          </div>
          <div className="dataset-summary">
            <div><small>Dataset ID</small><strong className="dataset-id">{result.dataset_id}</strong></div>
            <div><small>Columns</small><strong>{result.columns.length}</strong></div>
            <div><small>Preview rows</small><strong>{result.preview.length}</strong></div>
          </div>
          {result.warnings && result.warnings.length > 0 && (
            <div className="workflow-alert warning">
              <strong>Data quality warnings</strong>
              <ul>{result.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
            </div>
          )}
          <div className="preview-table-wrapper">
            <table className="preview-table">
              <thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
              <tbody>
                {result.preview.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {result.columns.map((column, columnIndex) => {
                      const value = Array.isArray(row) ? row[columnIndex] : row[column];
                      return <td key={column}>{formatCell(value)}</td>;
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.preview.length === 0 && <p className="empty-preview">The upload succeeded, but no preview rows were returned.</p>}
          <div className="workflow-actions">
            <button type="button" className="button button-primary" disabled={result.columns.length < 2} onClick={onContinue}>Continue to configuration →</button>
          </div>
        </section>
      )}
    </section>
  );
}
