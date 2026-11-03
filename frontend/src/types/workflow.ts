
export type WorkflowStep = "upload" | "configure" | "evaluate" | "results";

export const WORKFLOW_STEPS: {
  id: WorkflowStep;
  number: number;
  title: string;
  description: string;
}[] = [
  {
    id: "upload",
    number: 1,
    title: "Upload",
    description: "Prepare your dataset",
  },
  {
    id: "configure",
    number: 2,
    title: "Configure",
    description: "Choose evaluation settings",
  },
  {
    id: "evaluate",
    number: 3,
    title: "Evaluate",
    description: "Run your evaluation",
  },
  {
    id: "results",
    number: 4,
    title: "Results",
    description: "Review model performance",
  },
];
