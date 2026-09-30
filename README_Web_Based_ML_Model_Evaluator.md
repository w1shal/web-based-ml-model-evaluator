# Web Based ML Model Evaluator

A web-based machine learning model evaluation platform that allows users
to upload datasets, configure experiments, run supported
machine-learning algorithms, inspect evaluation metrics and
visualizations, and export results.

## Project Status

Academic software engineering project --- Team 14.

## Team

-   PES2UG24CS592
-   PES2UG24CS599
-   PES2UG24CS578
-   PES2UG24CS604

## Key Features

-   User registration and authentication
-   CSV dataset upload and validation
-   Dataset preview and validation warnings
-   Target and feature selection
-   Missing-value handling
-   Multi-algorithm evaluation
-   Supported algorithms:
    -   Logistic Regression
    -   Decision Tree
    -   Random Forest
    -   Support Vector Machine (SVM)
    -   K-Nearest Neighbors (KNN)
-   Evaluation metrics including accuracy, precision, recall, F1-score
    and applicable ROC-AUC
-   Confusion-matrix visualization
-   Algorithm comparison and ranking
-   PDF and CSV result export
-   Per-user evaluation history
-   Error handling and API-level validation
-   Security controls including authorization, input sanitization, rate
    limiting and secure transport

## Project Structure

Use the following structure as the repository is implemented:

``` text
web-based-ml-model-evaluator/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── docs/
│   ├── SRS/
│   │   └── SRS.pdf
│   ├── SAD/
│   │   └── SAD.pdf
│   └── Test-Plan/
│       └── Test_Plan_Web_Based_ML_Model_Evaluator.pdf
│
├── test-data/
│   ├── D1-iris.csv
│   ├── D2-breast-cancer.csv
│   └── ...
│
├── .gitignore
├── README.md
└── LICENSE
```

Adjust the structure if the final SADS architecture specifies different
module names.

## System Workflow

``` text
Dataset Upload
      ↓
Validation & Preview
      ↓
Experiment Configuration
      ↓
ML Evaluation Engine
      ↓
Metrics & Results
      ↓
Visualization
      ↓
PDF / CSV Export
      ↓
Authenticated History
```

## Technology Stack

The final implementation should follow the technologies selected in the
SRS/SADS.

Expected backend stack:

-   Python 3.11+
-   FastAPI or Flask
-   pandas
-   NumPy
-   scikit-learn
-   SQLite for development/CI
-   PostgreSQL for staging/deployment

Expected frontend:

-   Web-based frontend using the framework selected in the SRS/SADS.

## Installation

### 1. Clone the repository

``` bash
git clone https://github.com/<GITHUB-USERNAME>/<REPOSITORY-NAME>.git
cd <REPOSITORY-NAME>
```

### 2. Backend setup

``` bash
cd backend

python -m venv .venv
```

Windows:

``` powershell
.venv\Scripts\activate
```

Linux/macOS:

``` bash
source .venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

### 3. Frontend setup

``` bash
cd ../frontend
npm install
```

Run the frontend using the command defined by the final frontend
configuration, for example:

``` bash
npm run dev
```

### 4. Run the backend

Use the command defined by the selected backend framework. For FastAPI,
a typical development command is:

``` bash
uvicorn app.main:app --reload
```

## Testing

The project follows the formal Software Test Plan in:

``` text
docs/Test-Plan/Test_Plan_Web_Based_ML_Model_Evaluator.pdf
```

Testing covers:

-   Unit testing
-   Integration testing
-   API contract testing
-   End-to-end testing
-   Non-functional testing
-   Security testing
-   Requirements traceability

Example backend test command:

``` bash
pytest
```

Coverage:

``` bash
pytest --cov
```

## Test Data

The test plan defines D1--D10 datasets covering:

-   Iris multiclass evaluation
-   Breast Cancer Wisconsin binary evaluation
-   Performance-boundary data
-   Missing values
-   Categorical data
-   File-size boundaries
-   Malformed CSV files
-   Formula-injection inputs
-   Single-class and small-class edge cases

Do not commit sensitive or private datasets to the repository.

## Documentation

  Document                                       Location
  ---------------------------------------------- -------------------
  Software Requirements Specification            `docs/SRS/`
  Software Architecture / Design Specification   `docs/SAD/`
  Software Test Plan                             `docs/Test-Plan/`

## Git Workflow

Use feature branches rather than committing directly to `main`.

``` bash
git checkout -b feature/<short-description>
```

After implementing a change:

``` bash
git status
git add .
git commit -m "Add <short description>"
git push -u origin feature/<short-description>
```

Open a Pull Request on GitHub and request review before merging.

Suggested branch types:

``` text
feature/<name>
fix/<name>
docs/<name>
test/<name>
refactor/<name>
```

## Commit Convention

Use concise, descriptive commits:

``` text
feat: add dataset upload validation
fix: handle invalid split ratio
test: add metric accuracy tests
docs: update SRS documentation
refactor: isolate evaluation engine
```

## Security

Never commit:

-   API keys
-   Passwords
-   JWT secrets
-   Database credentials
-   `.env` files containing secrets
-   Private datasets
-   Local virtual environments

Use environment variables for configuration and add secret-containing
files to `.gitignore`.

## License

Add the license required by the project or course before publication.
