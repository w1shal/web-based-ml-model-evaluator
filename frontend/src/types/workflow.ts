export type WorkflowStep = "upload" | "configure" | "evaluate" | "results";

export interface UploadedDataset {
  dataset_id: string;
  name?: string;
  columns: string[];
  preview: Array<Record<string, unknown> | unknown[]>;
  warnings?: string[];
}

export interface EvaluationConfig {
  dataset_id: string;
  target_column: string;
  feature_columns: string[];
  algorithms: string[];
  test_size: number;
  missing_value_strategy: "median_imputation" | "drop_rows";
}

export interface EvaluationApiResult {
  algorithm: string;
  name?: string;
  status?: string;
  error?: string;
  accuracy?: number | null;
  precision?: number | null;
  recall?: number | null;
  f1_score?: number | null;
  roc_auc?: number | null;
  confusion_matrix?: number[][] | null;
  classes?: Array<string | number> | null;
  class_labels?: Array<string | number> | null;
}

export interface EvaluationApiResponse {
  run_id: string;
  status: string;
  dataset: {
    name?: string;
    rows?: number;
    train_rows?: number;
    test_rows?: number;
  };
  results: EvaluationApiResult[];
  preprocessing?: Record<string, unknown>;
}

export interface HistoryListItem {
  run_id: string;
  dataset_name: string;
  timestamp: string;
  status: string;
  algorithms: string[];
  metrics: Array<{
    algorithm: string;
    accuracy: number | null;
    precision: number | null;
    recall: number | null;
    f1_score: number | null;
    roc_auc: number | null;
  }>;
}

export interface HistoryListResponse {
  items: HistoryListItem[];
  total: number;
  limit: number;
  offset: number;
}

export const WORKFLOW_STEPS: {
  id: WorkflowStep;
  number: number;
  title: string;
  description: string;
}[] = [
  { id: "upload", number: 1, title: "Upload", description: "Prepare your dataset" },
  { id: "configure", number: 2, title: "Configure", description: "Choose evaluation settings" },
  { id: "evaluate", number: 3, title: "Evaluate", description: "Run your evaluation" },
  { id: "results", number: 4, title: "Results", description: "Review model performance" },
];
