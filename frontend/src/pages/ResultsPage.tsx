
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import type { EvaluationRunDetail, MetricKey } from "../types/results";

type SortDirection = "ascending" | "descending";
type ReportFormat = "csv" | "pdf";

type ResultsPageProps = {
  run: EvaluationRunDetail;
  token?: string | null;
  loading?: boolean;
  onClose?: () => void;
};

const METRICS: { key: MetricKey; label: string }[] = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1_score", label: "F1 score" },
  { key: "roc_auc", label: "ROC-AUC" },
];

function formatMetric(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "N/A";
  return `${(value * 100).toFixed(2)}%`;
}

function isMulticlass(run: EvaluationRunDetail, algorithm: string): boolean {
  const matrix = run.confusion_matrices[algorithm];
  const labels = run.confusion_matrix_labels?.[algorithm];
  return (matrix?.length ?? 0) > 2 || (labels?.length ?? 0) > 2;
}

function classLabels(run: EvaluationRunDetail, algorithm: string, size: number) {
  const provided =
    run.confusion_matrix_labels?.[algorithm] ??
    run.metrics.find((item) => item.algorithm === algorithm)?.class_labels;
  if (provided?.length === size) return provided;
  return Array.from({ length: size }, (_, index) => `Class ${index + 1}`);
}

function saveBlob(blob: Blob, runId: string, format: ReportFormat) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `evaluation-${runId}.${format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export default function ResultsPage({
  run,
  token,
  loading = false,
  onClose,
}: ResultsPageProps) {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>("accuracy");
  const [sortDirection, setSortDirection] = useState<SortDirection>("descending");
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("");
  const [reportBusy, setReportBusy] = useState<ReportFormat | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const availableMatrices = useMemo(
    () => run.metrics.filter((result) => {
      const matrix = run.confusion_matrices[result.algorithm];
      return Array.isArray(matrix) && matrix.length > 0 && matrix.every(
        (row) => Array.isArray(row) && row.length === matrix.length,
      );
    }),
    [run.confusion_matrices, run.metrics],
  );

  useEffect(() => {
    const selectedStillExists = availableMatrices.some(
      (result) => result.algorithm === selectedAlgorithm,
    );
    if (!selectedStillExists) {
      setSelectedAlgorithm(availableMatrices[0]?.algorithm ?? "");
    }
  }, [availableMatrices, selectedAlgorithm]);

  const sortedMetrics = useMemo(() => {
    return [...run.metrics].sort((left, right) => {
      const a = left[selectedMetric] ?? null;
      const b = right[selectedMetric] ?? null;
      if (a === null && b === null) return left.algorithm.localeCompare(right.algorithm);
      if (a === null) return 1;
      if (b === null) return -1;
      if (a === b) return left.algorithm.localeCompare(right.algorithm);
      return sortDirection === "ascending" ? a - b : b - a;
    });
  }, [run.metrics, selectedMetric, sortDirection]);

  const chartValues = run.metrics.map((result) => ({
    algorithm: result.algorithm,
    value: result[selectedMetric],
  }));
  const matrix = selectedAlgorithm
    ? run.confusion_matrices[selectedAlgorithm]
    : null;
  const labels = matrix
    ? classLabels(run, selectedAlgorithm, matrix.length)
    : [];
  const maximumCell = matrix
    ? Math.max(1, ...matrix.flat().filter((value) => Number.isFinite(value)))
    : 1;

  async function downloadReport(format: ReportFormat) {
    setReportBusy(format);
    setReportError(null);
    try {
      const blob = await api.downloadReport(run.run_id, format, token);
      saveBlob(blob, run.run_id, format);
    } catch (error) {
      setReportError(
        error instanceof Error ? error.message : `Unable to download the ${format.toUpperCase()} report.`,
      );
    } finally {
      setReportBusy(null);
    }
  }

  if (loading) {
    return (
      <section className="results-panel" aria-busy="true">
        <p className="results-status" role="status">Loading evaluation results…</p>
      </section>
    );
  }

  return (
    <section className="results-panel" aria-busy={reportBusy !== null}>
      <div className="results-heading">
        <div>
          <span className="eyebrow">COMPLETED EVALUATION</span>
          <h2>Results for {run.dataset_name}</h2>
          <p className="results-meta">
            Run {run.run_id} · Target: {run.target_column} · Test split: {(run.split_ratio * 100).toFixed(0)}%
          </p>
        </div>
        {onClose && (
          <button className="button button-outline" type="button" onClick={onClose}>
            Close results
          </button>
        )}
      </div>

      {reportError && <p className="notice notice-error" role="alert">{reportError}</p>}
      {reportBusy && (
        <p className="results-status" role="status" aria-live="polite">
          Preparing {reportBusy.toUpperCase()} report…
        </p>
      )}

      <section className="results-card" aria-labelledby="comparison-chart-title">
        <div className="results-card-heading">
          <div>
            <h3 id="comparison-chart-title">Metric comparison</h3>
            <p>Compare the selected metric across the evaluated algorithms.</p>
          </div>
          <label className="control-label" htmlFor="chart-metric">
            Metric
            <select
              id="chart-metric"
              value={selectedMetric}
              onChange={(event) => setSelectedMetric(event.target.value as MetricKey)}
            >
              {METRICS.map((metric) => (
                <option value={metric.key} key={metric.key}>{metric.label}</option>
              ))}
            </select>
          </label>
        </div>

        {chartValues.length === 0 ? (
          <p className="empty-results">No metric results are available for this run.</p>
        ) : (
          <div className="metric-chart" role="list" aria-label={`${METRICS.find((metric) => metric.key === selectedMetric)?.label} comparison across algorithms`}>
            {chartValues.map(({ algorithm, value }) => (
              <div className="metric-bar-row" role="listitem" key={algorithm}>
                <span className="metric-bar-label">{algorithm}</span>
                <div className="metric-track" aria-hidden="true">
                  <span
                    className="metric-bar"
                    style={{ width: `${value === null ? 0 : Math.max(0, Math.min(1, value)) * 100}%` }}
                  />
                </div>
                <span className="metric-bar-value">{formatMetric(value)}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="results-card" aria-labelledby="comparison-table-title">
        <div className="results-card-heading">
          <div>
            <h3 id="comparison-table-title">Model comparison</h3>
            <p>Sort by a metric. Equal values stay in alphabetical algorithm order.</p>
          </div>
          <div className="sort-controls">
            <label className="control-label" htmlFor="sort-metric">
              Sort by
              <select
                id="sort-metric"
                value={selectedMetric}
                onChange={(event) => setSelectedMetric(event.target.value as MetricKey)}
              >
                {METRICS.map((metric) => (
                  <option value={metric.key} key={metric.key}>{metric.label}</option>
                ))}
              </select>
            </label>
            <button
              className="button button-outline"
              type="button"
              aria-label={`Sort ${sortDirection === "descending" ? "ascending" : "descending"}`}
              onClick={() => setSortDirection((direction) => direction === "descending" ? "ascending" : "descending")}
            >
              {sortDirection === "descending" ? "Highest first" : "Lowest first"}
            </button>
          </div>
        </div>

        {run.metrics.length === 0 ? (
          <p className="empty-results">No model metrics are available.</p>
        ) : (
          <div className="table-scroll" role="region" aria-label="Model comparison table" tabIndex={0}>
            <table className="comparison-table" aria-label="Model comparison">
              <thead>
                <tr>
                  <th scope="col">Algorithm</th>
                  {METRICS.map((metric) => (
                    <th
                      scope="col"
                      key={metric.key}
                      aria-sort={selectedMetric === metric.key ? sortDirection : "none"}
                    >
                      {metric.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedMetrics.map((result) => (
                  <tr key={result.algorithm}>
                    <th scope="row">{result.algorithm}</th>
                    {METRICS.map((metric) => {
                      const value = result[metric.key];
                      const notApplicable = metric.key === "roc_auc" && value === null && isMulticlass(run, result.algorithm);
                      return (
                        <td key={metric.key}>
                          {notApplicable ? "N/A (multiclass)" : formatMetric(value)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="results-card" aria-labelledby="confusion-matrix-title">
        <div className="results-card-heading">
          <div>
            <h3 id="confusion-matrix-title">Confusion matrix</h3>
            <p>Rows show actual classes; columns show predicted classes.</p>
          </div>
          {availableMatrices.length > 1 && (
            <label className="control-label" htmlFor="matrix-algorithm">
              Algorithm
              <select
                id="matrix-algorithm"
                value={selectedAlgorithm}
                onChange={(event) => setSelectedAlgorithm(event.target.value)}
              >
                {availableMatrices.map((result) => (
                  <option value={result.algorithm} key={result.algorithm}>{result.algorithm}</option>
                ))}
              </select>
            </label>
          )}
        </div>

        {!matrix ? (
          <p className="empty-results">Confusion matrix data is unavailable for this evaluation.</p>
        ) : (
          <div className="table-scroll" role="region" aria-label="Confusion matrix" tabIndex={0}>
            <table className="confusion-table">
              <caption>{selectedAlgorithm} confusion matrix</caption>
              <thead>
                <tr>
                  <th scope="col">Actual \ Predicted</th>
                  {labels.map((label, index) => <th scope="col" key={`${label}-${index}`}>{label}</th>)}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row, rowIndex) => (
                  <tr key={`${labels[rowIndex]}-${rowIndex}`}>
                    <th scope="row">{labels[rowIndex]}</th>
                    {row.map((count, columnIndex) => {
                      const intensity = Math.max(0, Math.min(1, Number(count) / maximumCell));
                      return (
                        <td
                          key={`${rowIndex}-${columnIndex}`}
                          style={{ backgroundColor: `rgba(104, 87, 216, ${0.08 + intensity * 0.35})` }}
                          aria-label={`${labels[rowIndex]} predicted as ${labels[columnIndex]}: ${count}`}
                        >
                          {count}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="results-card report-actions" aria-labelledby="report-title">
        <div>
          <h3 id="report-title">Download this evaluation</h3>
          <p>Exports use the stored values for run {run.run_id}.</p>
        </div>
        <div className="report-buttons">
          <button type="button" className="button button-outline" disabled={reportBusy !== null} onClick={() => void downloadReport("csv")}>
            {reportBusy === "csv" ? "Preparing CSV…" : "Download CSV"}
          </button>
          <button type="button" className="button button-primary" disabled={reportBusy !== null} onClick={() => void downloadReport("pdf")}>
            {reportBusy === "pdf" ? "Preparing PDF…" : "Download PDF"}
          </button>
        </div>
      </section>
    </section>
  );
}
