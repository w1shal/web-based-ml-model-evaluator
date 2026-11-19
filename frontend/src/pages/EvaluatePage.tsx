import { useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import type { EvaluationApiResponse, EvaluationConfig } from "../types/workflow";

interface EvaluatePageProps {
  config: EvaluationConfig | null;
  datasetName?: string;
  token?: string | null;
  onEvaluationComplete: (result: EvaluationApiResponse) => void;
  onEditConfiguration: () => void;
}

export default function EvaluatePage({ config, datasetName, token, onEvaluationComplete, onEditConfiguration }: EvaluatePageProps) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function runEvaluation() {
    if (!config || running) return;
    setRunning(true);
    setError("");
    try {
      const response = await apiRequest<EvaluationApiResponse>("/evaluations", {
        method: "POST",
        body: JSON.stringify(config),
        token,
      });
      if (!response || !response.run_id || !Array.isArray(response.results)) {
        throw new Error("The backend returned an incomplete evaluation response.");
      }
      onEvaluationComplete(response);
    } catch (runError) {
      setError(runError instanceof ApiError ? runError.message : runError instanceof Error ? runError.message : "The evaluation could not be completed.");
    } finally {
      setRunning(false);
    }
  }

  if (!config) {
    return (
      <section className="workflow-page">
        <div className="workflow-page-heading"><span className="eyebrow">STEP 03 · MODEL RUN</span><h2>Evaluate your models</h2><p>Validate your configuration before starting an evaluation.</p></div>
        <div className="workflow-alert warning">No valid configuration is available. Go back to Configure to select a target, features, and algorithms.</div>
        <button type="button" className="button button-outline" onClick={onEditConfiguration}>Back to configuration</button>
      </section>
    );
  }

  const algorithmNames: Record<string, string> = {
    logistic_regression: "Logistic Regression",
    decision_tree: "Decision Tree",
    random_forest: "Random Forest",
    svm: "Support Vector Machine",
    knn: "K-Nearest Neighbors",
  };

  return (
    <section className="workflow-page">
      <div className="workflow-page-heading">
        <span className="eyebrow">STEP 03 · MODEL EXECUTION</span>
        <h2>Ready to evaluate</h2>
        <p>The backend will load the stored dataset, preprocess the selected features, perform a stratified train/test split, train each algorithm, and persist the resulting run for authenticated users.</p>
      </div>
      <div className="evaluation-summary">
        <div><small>Dataset</small><strong>{datasetName || config.dataset_id}</strong></div>
        <div><small>Prediction target</small><strong>{config.target_column}</strong></div>
        <div><small>Feature columns</small><strong>{config.feature_columns.length}</strong></div>
        <div><small>Algorithms</small><strong>{config.algorithms.length}</strong></div>
        <div><small>Training rows</small><strong>{100 - config.test_size * 100}%</strong></div>
        <div><small>Testing rows</small><strong>{config.test_size * 100}%</strong></div>
        <div className="evaluation-algorithms">
          <small>Selected algorithms</small>
          <div>{config.algorithms.map((id) => <span className="algorithm-chip" key={id}>{algorithmNames[id] || id}</span>)}</div>
        </div>
      </div>
      {error && <div className="workflow-alert error" role="alert">{error}</div>}
      {running && <div className="workflow-alert info" role="status">Evaluation is running. Training models and calculating metrics… Keep this tab open.</div>}
      <div className="workflow-actions">
        <button type="button" className="button button-outline" disabled={running} onClick={onEditConfiguration}>Edit configuration</button>
        <button type="button" className="button button-primary" disabled={running} onClick={() => void runEvaluation()}>{running ? "Running evaluation…" : "Run evaluation →"}</button>
      </div>
    </section>
  );
}
