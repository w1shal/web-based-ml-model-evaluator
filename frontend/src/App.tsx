
import { useState } from "react";
import StepNavigation from "./components/StepNavigation";
import UploadPage from "./pages/UploadPage";
import ConfigurePage from "./pages/ConfigurePage";
import EvaluatePage from "./pages/EvaluatePage";
import ResultsPage from "./pages/ResultsPage";
import type {
  EvaluationConfig,
  UploadedDataset,
  WorkflowStep,
} from "./types/workflow";
import "./App.css";


export default function App() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>("upload");
 const [uploadedDataset, setUploadedDataset] =
  useState<UploadedDataset | null>(null);
 const [evaluationConfig, setEvaluationConfig] =
  useState<EvaluationConfig | null>(null);

const pageContent: Record<
  WorkflowStep,
  { title: string; component: React.ReactNode }
> = {
  upload: {
  title: "New evaluation",
  component: (
    <UploadPage onUploadSuccess={setUploadedDataset} />
  ),
},
  configure: {
  title: "Configure evaluation",
  component: (
    <ConfigurePage
      dataset={uploadedDataset}
      onConfigChange={setEvaluationConfig}
    />
  ),
},
  evaluate: {
    title: "Run evaluation",
    component: <EvaluatePage config={evaluationConfig} />,
  },
  results: {
    title: "Evaluation results",
    component: <ResultsPage />,
  },
};


  const activePage = pageContent[currentStep];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="Model Evaluator home">
          <span className="brand-mark">M</span>
          <span>
            <strong>Model Evaluator</strong>
            <small>ML WORKSPACE</small>
          </span>
        </a>

        <div className="sidebar-label">WORKSPACE</div>

        <button className="sidebar-link selected" type="button">
          <span>▦</span> Model evaluation
        </button>

        <div className="sidebar-note">
          <span className="status-dot" />
          <div>
            <strong>Evaluation workspace</strong>
            <p>Your models, one workflow.</p>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="avatar">G</span>
          <div>
            <strong>Guest workspace</strong>
            <small>Local session</small>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace / </span>
            <strong>{activePage.title}</strong>
          </div>
          <span className="environment-tag">
            <span className="status-dot" /> Development
          </span>
        </header>

        <div className="content-area">
          <section className="welcome-section">
            <div>
              <span className="eyebrow">ML MODEL EVALUATOR</span>
              <h1>Evaluate models with confidence.</h1>
              <p>
                A structured workspace to prepare datasets, configure
                experiments, and compare model performance.
              </p>
            </div>
              <div className="welcome-decoration" aria-hidden="true">
                <span>ML</span>
                <i />
                <i />
                <i />
              </div>
          </section>

          <section className="workflow-card">
            <div className="workflow-heading">
              <div>
                <h2>Your workflow</h2>
                <p>Move through each stage of your evaluation.</p>
              </div>
              <span className="step-count">
                STEP{" "}
                {["upload", "configure", "evaluate", "results"].indexOf(
                  currentStep,
                ) + 1}{" "}
                OF 4
              </span>
            </div>

            <StepNavigation
  currentStep={currentStep}
  onStepChange={(step) => {
    if (step !== "upload" && !uploadedDataset) {
      return;
    }

    if (
      (step === "evaluate" || step === "results") &&
      !evaluationConfig
    ) {
      return;
    }

    setCurrentStep(step);
  }}
/>

            <div className="page-divider" />

            {activePage.component}

            <footer className="workflow-footer">
              <span>
                <span className="status-dot" /> Your progress is local
              </span>

              <div className="footer-actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={currentStep === "upload"}
                  onClick={() => {
                    const steps: WorkflowStep[] = [
                      "upload",
                      "configure",
                      "evaluate",
                      "results",
                    ];
                    setCurrentStep(steps[steps.indexOf(currentStep) - 1]);
                  }}
                >
                  Back
                </button>

                <button
  className="button-primary"
  type="button"
  disabled={
    currentStep === "results" ||
    (currentStep === "upload" && !uploadedDataset) ||
    (currentStep === "configure" && !evaluationConfig)
  }
  onClick={() => {
    const steps: WorkflowStep[] = [
      "upload",
      "configure",
      "evaluate",
      "results",
    ];

    setCurrentStep(steps[steps.indexOf(currentStep) + 1]);
  }}
>
  Next step <span aria-hidden="true">→</span>
</button>
              </div>
            </footer>
          </section>

          <p className="page-footnote">
            Built for transparent and reproducible machine learning evaluation.
          </p>
        </div>
      </main>
    </div>
  );
}
