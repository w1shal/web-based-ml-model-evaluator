# Sprint 2 results and reports

## Report endpoints

- `GET /reports/{run_id}/csv` downloads the stored metrics and evaluation configuration as CSV.
- `GET /reports/{run_id}/pdf` downloads the dataset, configuration, metrics, and a short best-model summary as PDF.
- Reports are generated only for completed runs. An unknown run, or a run owned by another account, returns `404`.
- Guest runs can be exported without signing in. A signed-in user's run is only available to that user.
- CSV text cells that begin with spreadsheet formula characters are escaped at export time. Stored values remain unchanged.

## Results screen

Sign in, enter a saved evaluation run ID, and choose **Open results**. The screen compares the five stored metrics, shows the selected metric as a bar chart, displays the class labels and counts from the confusion matrix, and offers CSV and PDF downloads. Missing metric or matrix data is shown as unavailable.

## Automated checks

The CI workflow runs the backend test suite, frontend TypeScript/Vite build, and frontend component tests. For a local run, use the setup steps in the root README.

## Cross-browser check record

Complete this table against the running application before marking the manual cross-browser check complete. Record the browser version and viewport used.

| Environment | Browser/version | Viewport | Status | Notes |
|---|---|---:|---|---|
| Desktop | Chrome | — | Pending | Sign in, open a saved run, sort metrics, inspect the matrix, download both reports. |
| Desktop | Firefox | — | Pending | Repeat the main results flow and check errors and focus indicators. |
| Desktop | Edge | — | Pending | Repeat the main results flow and check errors and focus indicators. |
| Tablet | Record browser/version | 768 × 1024 | Pending | Check the header, controls, chart labels, and horizontally scrollable tables. |

### Manual pass criteria

1. Keyboard users can reach the run ID field, result controls, table regions, and report buttons, with a visible focus outline.
2. The results page shows the same selected metric values in the chart and comparison table.
3. Sorting works in both directions and keeps ties in alphabetical algorithm order.
4. Class labels and counts align with the stored confusion matrix; unavailable data is identified clearly.
5. CSV and PDF files download with the run's values and expected file type.
6. The layout stays readable at desktop and tablet widths, and loading/error states are understandable.
