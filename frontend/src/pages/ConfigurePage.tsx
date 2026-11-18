import { useState } from "react";
import type { EvaluationConfig, UploadedDataset } from "../types/workflow";

interface ConfigurePageProps {
  dataset: UploadedDataset | null;
  onConfigChange: (config: EvaluationConfig | null) => void;
  onContinue: () => void;
  onBack: () => void;
}

const ALGORITHMS = [
  { id: "logistic_regression", label: "Logistic Regression" },
  { id: "decision_tree", label: "Decision Tree" },
  { id: "random_forest", label: "Random Forest" },
  { id: "svm", label: "Support Vector Machine (SVM)" },
  { id: "knn", label: "K-Nearest Neighbors (KNN)" },
];

export default function ConfigurePage({ dataset, onConfigChange, onContinue, onBack }: ConfigurePageProps) {
  const initialTarget = dataset?.columns[dataset.columns.length - 1] ?? "";
  const [targetColumn, setTargetColumn] = useState(initialTarget);
  const [featureColumns, setFeatureColumns] = useState<string[]>(
    dataset ? dataset.columns.filter((column) => column !== initialTarget) : [],
  );
  const [algorithms, setAlgorithms] = useState<string[]>(["logistic_regression"]);
  const [testSize, setTestSize] = useState(20);
  const [missingStrategy, setMissingStrategy] = useState<"median_imputation" | "drop_rows">("median_imputation");
  const [error, setError] = useState("");
  const [validated, setValidated] = useState(false);

  if (!dataset) {
    return (
      <section className="workflow-page">
        <div className="workflow-page-heading"><span className="eyebrow">STEP 02 · SETTINGS</span><h2>Configure your evaluation</h2><p>Upload a dataset before choosing your target and features.</p></div>
        <div className="workflow-alert warning">No dataset is loaded. Return to Upload to select a CSV file.</div>
      </section>
    );
  }

  function invalidate() {
    setValidated(false);
    onConfigChange(null);
    setError("");
  }

  function validateAndContinue() {
    if (!dataset) {
      setError("Upload a dataset before validating the configuration.");
      return;
    }
    let message = "";
    if (!targetColumn) message = "Choose the target column that the model should predict.";
    else if (featureColumns.length === 0) message = "Select at least one feature column.";
    else if (featureColumns.includes(targetColumn)) message = "The target column cannot also be used as a feature.";
    else if (algorithms.length === 0) message = "Select at least one algorithm.";
    else if (testSize < 5 || testSize > 50) message = "The test split must be between 5% and 50%.";
    if (message) {
      setError(message);
      setValidated(false);
      onConfigChange(null);
      return;
    }
    const config: EvaluationConfig = {
      dataset_id: dataset.dataset_id,
      target_column: targetColumn,
      feature_columns: featureColumns,
      algorithms,
      test_size: testSize / 100,
      missing_value_strategy: missingStrategy,
    };
    onConfigChange(config);
    setValidated(true);
    setError("");
  }

  return (
    <section className="workflow-page">
      <div className="workflow-page-heading">
        <span className="eyebrow">STEP 02 · EXPERIMENT SETTINGS</span>
        <h2>Configure your evaluation</h2>
        <p>Choose the target, input features, algorithms, and hold-out split for this classification experiment.</p>
      </div>

      <div className="dataset-context">
        <div><small>Dataset</small><strong>{dataset.name || dataset.dataset_id}</strong></div>
        <div><small>Available columns</small><strong>{dataset.columns.length}</strong></div>
        <div><small>Dataset ID</small><strong className="dataset-id">{dataset.dataset_id}</strong></div>
      </div>

      <div className="configuration-card">
        <div className="configuration-section">
          <span className="section-index">01</span>
          <div className="configuration-copy">
            <h3>Prediction target</h3>
            <p>Select the column containing the class label you want to predict.</p>
            <label className="field-label" htmlFor="target-column">Target column</label>
            <select id="target-column" className="workflow-select" value={targetColumn} onChange={(event) => {
              const nextTarget = event.target.value;
              setFeatureColumns((current) => current.filter((column) => column !== nextTarget));
              setTargetColumn(nextTarget);
              invalidate();
            }}>
              <option value="">Choose target column</option>
              {dataset.columns.map((column) => <option value={column} key={column}>{column}</option>)}
            </select>
          </div>
        </div>

        <div className="configuration-section">
          <span className="section-index">02</span>
          <div className="configuration-copy">
            <h3>Input features</h3>
            <p>Select the columns the algorithms may use. The target cannot be selected as an input.</p>
            <div className="option-grid">
              {dataset.columns.map((column) => (
                <label className={"configuration-option" + (column === targetColumn ? " is-target" : "")} key={column}>
                  <input
                    type="checkbox"
                    checked={featureColumns.includes(column)}
                    disabled={column === targetColumn}
                    onChange={() => {
                      setFeatureColumns((current) => current.includes(column) ? current.filter((item) => item !== column) : [...current, column]);
                      invalidate();
                    }}
                  />
                  <span>{column}</span>
                  {column === targetColumn && <small>Target</small>}
                </label>
              ))}
            </div>
            <small className="field-hint">{featureColumns.length} feature column(s) selected</small>
          </div>
        </div>

        <div className="configuration-section">
          <span className="section-index">03</span>
          <div className="configuration-copy">
            <h3>Algorithms</h3>
            <p>Select one or more classification algorithms to compare in the same run.</p>
            <div className="option-grid">
              {ALGORITHMS.map((algorithm) => (
                <label className="configuration-option" key={algorithm.id}>
                  <input type="checkbox" checked={algorithms.includes(algorithm.id)} onChange={() => {
                    setAlgorithms((current) => current.includes(algorithm.id) ? current.filter((item) => item !== algorithm.id) : [...current, algorithm.id]);
                    invalidate();
                  }} />
                  <span>{algorithm.label}</span>
                </label>
              ))}
            </div>
            <small className="field-hint">{algorithms.length} of 5 algorithms selected</small>
          </div>
        </div>

        <div className="configuration-section">
          <span className="section-index">04</span>
          <div className="configuration-copy">
            <h3>Train / test split</h3>
            <p>Choose the percentage of usable rows reserved for final testing.</p>
            <div className="range-heading"><label htmlFor="test-size">Test data</label><strong>{testSize}%</strong></div>
            <input id="test-size" className="workflow-range" type="range" min="5" max="50" step="5" value={testSize} onChange={(event) => {
              setTestSize(Number(event.target.value));
              invalidate();
            }} />
            <div className="split-summary"><span>Training: {100 - testSize}%</span><span>Testing: {testSize}%</span></div>
          </div>
        </div>

        <div className="configuration-section">
          <span className="section-index">05</span>
          <div className="configuration-copy">
            <h3>Missing-value handling</h3>
            <p>Choose how missing input-feature values are handled before training.</p>
            <label className="field-label" htmlFor="missing-strategy">Strategy</label>
            <select id="missing-strategy" className="workflow-select" value={missingStrategy} onChange={(event) => {
              setMissingStrategy(event.target.value as "median_imputation" | "drop_rows");
              invalidate();
            }}>
              <option value="median_imputation">Impute missing values (median / most frequent)</option>
              <option value="drop_rows">Drop rows containing missing feature values</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="workflow-alert error" role="alert">{error}</div>}
      {validated && <div className="workflow-alert success" role="status">Configuration validated. You can proceed to run the selected algorithms.</div>}
      <div className="workflow-actions">
        <button type="button" className="button button-outline" onClick={onBack}>Back to upload</button>
        <button type="button" className="button button-primary" onClick={validateAndContinue}>Validate configuration</button>
        <button type="button" className="button button-primary" disabled={!validated} onClick={onContinue}>Continue to evaluation →</button>
      </div>
    </section>
  );
}
