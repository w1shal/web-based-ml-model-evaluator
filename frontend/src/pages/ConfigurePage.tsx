import { useState } from "react";
import type {
  UploadedDataset,
  EvaluationConfig,
} from "../types/workflow";

interface ConfigurePageProps {
  dataset: UploadedDataset | null;
  onConfigChange: (config: EvaluationConfig | null) => void;
}

const ALGORITHMS = [
  { id: "logistic_regression", label: "Logistic Regression" },
  { id: "decision_tree", label: "Decision Tree" },
  { id: "random_forest", label: "Random Forest" },
  { id: "svm", label: "Support Vector Machine (SVM)" },
  { id: "knn", label: "K-Nearest Neighbors (KNN)" },
];

export default function ConfigurePage({
  dataset,
  onConfigChange,
}: ConfigurePageProps) {
  const [targetColumn, setTargetColumn] = useState(
  dataset?.columns[0] ?? "",
);
const [featureColumns, setFeatureColumns] = useState<string[]>(
  dataset?.columns.slice(1) ?? [],
);
const [algorithms, setAlgorithms] = useState<string[]>([
  "logistic_regression",
]);
const [testSize, setTestSize] = useState(20);
const [error, setError] = useState("");

  if (!dataset) {
    return (
      <section className="page-content">
        <span className="eyebrow">STEP 02</span>
        <h2>Configure your evaluation</h2>
        <p>Please upload a dataset before configuring your evaluation.</p>
      </section>
    );
  }

  function validateConfiguration(): string {
    if (!targetColumn) {
      return "Please select a target column.";
    }

    if (featureColumns.length === 0) {
      return "Please select at least one feature column.";
    }

    if (featureColumns.includes(targetColumn)) {
      return "The target column cannot also be a feature.";
    }

    if (algorithms.length === 0 || algorithms.length > 5) {
      return "Please select between 1 and 5 algorithms.";
    }

    if (testSize < 10 || testSize > 50) {
      return "Test split must be between 10% and 50%.";
    }

    return "";
  }

  function toggleFeature(column: string) {
    onConfigChange(null);
    setFeatureColumns((current) =>
      current.includes(column)
        ? current.filter((item) => item !== column)
        : [...current, column],
    );
    setError("");
  }

  function toggleAlgorithm(algorithm: string) {
    onConfigChange(null);
    setAlgorithms((current) =>
      current.includes(algorithm)
        ? current.filter((item) => item !== algorithm)
        : [...current, algorithm],
    );
    setError("");
  }

  function handleConfigurationChange() {
  if (!dataset) return;

  const validationError = validateConfiguration();
    setError(validationError);

    if (validationError) {
      onConfigChange(null);
      return;
    }

    onConfigChange({
      dataset_id: dataset.dataset_id,
      target_column: targetColumn,
      feature_columns: featureColumns,
      algorithms,
      test_size: testSize / 100,
      missing_value_strategy: "median_imputation",
    });
  }

  return (
    <section className="page-content configure-page">
      <span className="eyebrow">STEP 02</span>
      <h2>Configure your evaluation</h2>
      <p>
        Choose what your model should predict, which features it can use,
        and which algorithms you want to compare.
      </p>

      <div className="placeholder-panel">
        <h3>Dataset information</h3>
        <p>Dataset ID: {dataset.dataset_id}</p>
        <p>Available columns: {dataset.columns.length}</p>
      </div>

      <div className="configuration-section">
        <h3>1. Select target column</h3>
        <p>Choose the column your machine learning models should predict.</p>

        <select
          value={targetColumn}
          onChange={(event) => {
            const nextTarget = event.target.value;
            onConfigChange(null);
            setTargetColumn(nextTarget);
            setFeatureColumns((current) =>
              current.filter((column) => column !== nextTarget),
            );
            setError("");
          }}
        >
          <option value="">Select target column</option>
          {dataset.columns.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))}
        </select>
      </div>

      <div className="configuration-section">
        <h3>2. Select feature columns</h3>
        <p>
          Choose the input columns your models can use. The target column
          cannot be selected as a feature.
        </p>

        <div className="configuration-options">
          {dataset.columns.map((column) => (
            <label key={column} className="configuration-option">
              <input
                type="checkbox"
                checked={featureColumns.includes(column)}
                disabled={column === targetColumn}
                onChange={() => toggleFeature(column)}
              />
              <span>{column}</span>
              {column === targetColumn && (
                <small>Target column</small>
              )}
            </label>
          ))}
        </div>
      </div>

      <div className="configuration-section">
        <h3>3. Select algorithms</h3>
        <p>Select between one and five algorithms to compare.</p>

        <div className="configuration-options">
          {ALGORITHMS.map((algorithm) => (
            <label key={algorithm.id} className="configuration-option">
              <input
                type="checkbox"
                checked={algorithms.includes(algorithm.id)}
                onChange={() => toggleAlgorithm(algorithm.id)}
              />
              <span>{algorithm.label}</span>
            </label>
          ))}
        </div>

        <small>{algorithms.length} of 5 algorithms selected</small>
      </div>

      <div className="configuration-section">
        <h3>4. Train/test split</h3>
        <p>Choose how much of your dataset should be used for testing.</p>

        <input
          type="range"
          min="10"
          max="50"
          step="5"
          value={testSize}
          onChange={(event) => {
  onConfigChange(null);
  setTestSize(Number(event.target.value));
  setError("");
}}
        />

        <div className="split-summary">
          <span>Training: {100 - testSize}%</span>
          <span>Testing: {testSize}%</span>
        </div>
      </div>

      <div className="configuration-section">
        <h3>5. Missing-value handling</h3>
        <p>
          Missing values will be handled using median imputation,
          following the example configuration in the project SAD.
        </p>
      </div>

      {error && (
        <div className="upload-error" role="alert">
          <strong>Configuration incomplete</strong>
          <span>{error}</span>
        </div>
      )}

      <button
        type="button"
        className="button-primary"
        onClick={handleConfigurationChange}
      >
        Validate configuration
      </button>
    </section>
  );
}