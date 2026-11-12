export type MetricKey = "accuracy" | "precision" | "recall" | "f1_score" | "roc_auc";

export type AlgorithmMetrics = {
  algorithm: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  roc_auc: number | null;
  class_labels?: string[] | null;
};

export type EvaluationRunDetail = {
  run_id: string;
  dataset_name: string;
  timestamp: string;
  status: string;
  algorithms: string[];
  metrics: AlgorithmMetrics[];
  target_column: string;
  feature_columns: string[];
  split_ratio: number;
  confusion_matrices: Record<string, number[][] | null>;
  confusion_matrix_labels?: Record<string, string[] | null>;
};
