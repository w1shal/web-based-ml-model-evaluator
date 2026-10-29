# ML Model Evaluator â€” Frontend

A responsive React and TypeScript frontend for the ML Model Evaluator project, built with Vite.

## Workflow

The interface contains four steps:

1. **Upload** â€” Entry point for providing a dataset.
2. **Configure** â€” Placeholder for evaluation settings.
3. **Evaluate** â€” Placeholder for running an evaluation.
4. **Results** â€” Placeholder for viewing evaluation results.

This issue provides the frontend scaffold and navigation. Detailed upload previews, configuration controls, evaluation execution, and results visualizations are planned for later issues.

## Requirements

- Node.js and npm
- The backend API, if you want to connect the frontend to the backend

## Installation

From the repository root:

```bash
cd frontend
npm install
```

## Configuration

Create a `.env.local` file in the `frontend` directory with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Change the URL if your backend runs elsewhere. Restart the Vite development server after changing environment variables.

**Security:** Variables prefixed with `VITE_` are exposed to browser code. Do not put passwords, private API keys, or other secrets in them.

The shared API client supports an optional Bearer token supplied directly to the helper or read from the browser's `localStorage` key `authToken`.

## Development server

From the `frontend` directory:

```bash
npm run dev
```

Open the local URL printed in the terminal, usually `http://localhost:5173/`.

## Production build

```bash
npm run build
```

## TypeScript check

```bash
npx tsc --noEmit -p tsconfig.app.json
```

## Project structure

```text
frontend/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api/client.ts
â”‚   â”œâ”€â”€ components/StepNavigation.tsx
â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”œâ”€â”€ UploadPage.tsx
â”‚   â”‚   â”œâ”€â”€ ConfigurePage.tsx
â”‚   â”‚   â”œâ”€â”€ EvaluatePage.tsx
â”‚   â”‚   â””â”€â”€ ResultsPage.tsx
â”‚   â”œâ”€â”€ types/workflow.ts
â”‚   â”œâ”€â”€ App.tsx
â”‚   â”œâ”€â”€ App.css
â”‚   â””â”€â”€ index.css
â”œâ”€â”€ package.json
â””â”€â”€ README.md
```
