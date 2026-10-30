import type { EvaluationResponse } from "../types/workflow";

interface ResultsPageProps {
  data: EvaluationResponse | null;
  loading?: boolean;
  error?: string | null;
}

function formatMetric(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }

  return `${(value * 100).toFixed(2)}%`;
}

export default function ResultsPage({
  data,
  loading = false,
  error = null,
}: ResultsPageProps) {
  if (loading) {
    return (
      <section className="page-content">
        <span className="eyebrow">STEP 04</span>
        <h2>Your evaluation results</h2>
        <div className="results-state" role="status">
          Loading evaluation results...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="page-content">
        <span className="eyebrow">STEP 04</span>
        <h2>Your evaluation results</h2>
        <div className="results-state results-error" role="alert">
          <strong>Evaluation failed</strong>
          <p>{error}</p>
        </div>
      </section>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <section className="page-content">
        <span className="eyebrow">STEP 04</span>
        <h2>Your evaluation results</h2>
        <div className="results-state" role="status">
          <h3>No evaluation results available</h3>
          <p>Complete an evaluation to see model performance metrics here.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="page-content">
      <span className="eyebrow">STEP 04</span>
      <h2>Your evaluation results</h2>
      <p>Compare the performance of your evaluated machine learning models.</p>

      <div className="results-section">
        <div className="preview-heading">
          <div>
            <span className="eyebrow">EVALUATION SUMMARY</span>
            <h3>Model performance</h3>
          </div>
          <span className="success-label">{data.results.length} models evaluated</span>
        </div>

        <p className="results-summary">
          Run ID: {data.run_id}
        </p>

        <div className="results-table-wrapper">
          <table className="results-table">
            <thead>
              <tr>
                <th scope="col">Algorithm</th>
                <th scope="col">Accuracy</th>
                <th scope="col">Precision</th>
                <th scope="col">Recall</th>
                <th scope="col">F1 Score</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((result) => (
                <tr key={result.algorithm}>
                  <td>{result.algorithm.replaceAll("_", " ")}</td>
                  <td>{formatMetric(result.accuracy)}</td>
                  <td>{formatMetric(result.precision)}</td>
                  <td>{formatMetric(result.recall)}</td>
                  <td>{formatMetric(result.f1_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}