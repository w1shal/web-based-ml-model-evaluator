import type { EvaluationConfig } from "../types/workflow";

interface EvaluatePageProps {
  config: EvaluationConfig | null;
}

export default function EvaluatePage({ config }: EvaluatePageProps) {
  return (
    <section className="page-content">
      <span className="eyebrow">STEP 03</span>
      <h2>Evaluate your models</h2>
      <p>Run the evaluation after preparing your dataset and settings.</p>

      {config ? (
        <div className="placeholder-panel">
          <span className="placeholder-icon">▶</span>
          <h3>Configuration ready</h3>
          <p>Target column: {config.target_column}</p>
          <p>Feature columns: {config.feature_columns.join(", ")}</p>
          <p>Algorithms: {config.algorithms.join(", ")}</p>
          <p>Training split: {(1 - config.test_size) * 100}%</p>
          <p>Testing split: {config.test_size * 100}%</p>
          <p>
            Evaluation execution will be connected to the backend in a
            later issue.
          </p>
        </div>
      ) : (
        <div className="placeholder-panel">
          <h3>Configuration required</h3>
          <p>Please complete and validate your configuration first.</p>
        </div>
      )}
    </section>
  );
}