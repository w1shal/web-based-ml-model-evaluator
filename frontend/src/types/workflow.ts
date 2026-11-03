export type WorkflowStep = "upload" | "configure" | "evaluate" | "results";

export interface UploadedDataset {
  dataset_id: string;
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
  missing_value_strategy: string;
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