
import { WORKFLOW_STEPS, type WorkflowStep } from "../types/workflow";

interface StepNavigationProps {
  currentStep: WorkflowStep;
  onStepChange: (step: WorkflowStep) => void;
}

export default function StepNavigation({
  currentStep,
  onStepChange,
}: StepNavigationProps) {
  const currentIndex = WORKFLOW_STEPS.findIndex(
    (step) => step.id === currentStep,
  );

  return (
    <nav className="workflow-nav" aria-label="Evaluation workflow">
      {WORKFLOW_STEPS.map((step, index) => {
        const isCurrent = step.id === currentStep;
        const isComplete = index < currentIndex;

        return (
          <button
            key={step.id}
            type="button"
            className={[
              "workflow-step",
              isCurrent ? "active" : "",
              isComplete ? "complete" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onStepChange(step.id)}
            aria-current={isCurrent ? "step" : undefined}
          >
            <span className="step-number">
              {isComplete ? "✓" : step.number}
            </span>

            <span className="step-copy">
              <span className="step-title">{step.title}</span>
              <span className="step-description">
                {step.description}
              </span>
            </span>
          </button>
        );
      })}
    </nav>
  );
}
