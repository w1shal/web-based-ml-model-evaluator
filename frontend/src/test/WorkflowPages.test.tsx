import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ConfigurePage from "../pages/ConfigurePage";
import EvaluatePage from "../pages/EvaluatePage";
import UploadPage from "../pages/UploadPage";

describe("Workflow placeholder pages", () => {
  it.each([
    ["Upload", UploadPage, "STEP 01", "Upload your dataset"],
    ["Configure", ConfigurePage, "STEP 02", "Configure your evaluation"],
    ["Evaluate", EvaluatePage, "STEP 03", "Evaluate your models"],
  ])("%s page renders its step label and heading", (_name, Page, step, heading) => {
    render(<Page />);
    expect(screen.getByText(step)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: heading })).toBeInTheDocument();
  });
});
