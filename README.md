# Web Based ML Model Evaluator

<p align="center">
  <strong>A web-based platform for evaluating and comparing machine learning algorithms on user-provided datasets.</strong>
</p>

<p align="center">
  Upload Dataset • Configure Evaluation • Evaluate Models • Analyze Metrics • Visualize Results • Export Reports
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Project-Web%20Based%20ML%20Model%20Evaluator-blue" alt="Project">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/scikit--learn-ML%20Engine-F7931E?logo=scikit-learn&logoColor=white" alt="Scikit-learn">
  <img src="https://img.shields.io/badge/Status-Under%20Development-yellow" alt="Status">
</p>

---

## 📌 Project Overview

The **Web Based ML Model Evaluator** is a web application that allows users to evaluate machine learning classification algorithms using their own datasets.

The system provides an end-to-end workflow starting from dataset upload and validation, followed by experiment configuration, model evaluation, metric calculation, visualization, and report generation.

Users can evaluate multiple algorithms on the same dataset and compare their performance using standardized evaluation metrics.

The application also provides authenticated users with access to their previous evaluation results.

---

## 🎯 Objectives

The primary objectives of the system are to:

- Provide a simple web interface for machine learning model evaluation.
- Allow users to upload and validate CSV datasets.
- Allow users to select target and feature columns.
- Provide configurable evaluation settings.
- Support multiple machine learning classification algorithms.
- Calculate and display standard evaluation metrics.
- Provide visual comparison of model performance.
- Generate downloadable evaluation reports.
- Maintain evaluation history for authenticated users.
- Apply validation and security controls to user-provided data and requests.

---

## ✨ Key Features

### 🔐 User Authentication

- User registration
- User login
- Secure password hashing
- Token-based authentication
- Logout and session invalidation
- Protected user-specific resources

### 📂 Dataset Upload and Validation

- CSV dataset upload
- File type validation
- File size validation
- Dataset parsing
- Dataset preview
- Column validation
- Missing-value detection
- Malformed CSV detection
- Encoding and delimiter handling
- Validation of uploaded content

### ⚙️ Evaluation Configuration

Users can configure an evaluation by specifying:

- Target column
- Feature columns
- Missing-value handling strategy
- Train/test split ratio
- One or more machine learning algorithms

The system validates the configuration before starting an evaluation.

### 🤖 Supported Algorithms

The evaluator supports the following built-in classification algorithms:

| Algorithm | Category |
|---|---|
| Logistic Regression | Classification |
| Decision Tree | Classification |
| Random Forest | Classification |
| Support Vector Machine (SVM) | Classification |
| K-Nearest Neighbors (KNN) | Classification |

Multiple algorithms can be selected and evaluated within a single evaluation run.

---

## 📊 Evaluation Metrics

The system calculates and displays relevant machine learning evaluation metrics, including:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC where applicable
- Confusion matrix

Metric calculations are validated against reference results using controlled random states.

For multiclass datasets, the applicable averaging method is documented and applied consistently.

Metrics that are not applicable to a particular evaluation scenario are explicitly identified rather than silently producing incorrect results.

---

## 📈 Result Visualization

The application provides visual representations of evaluation results, including:

### Algorithm Comparison

Comparison of metrics across multiple evaluated algorithms.

### Confusion Matrix

A confusion-matrix visualization showing:

- Class labels
- Predicted results
- Actual results
- Class-wise counts

### Algorithm Ranking

A ranking table comparing algorithms using the documented ranking metric.

### Metric Applicability

The interface indicates when a metric such as ROC-AUC is not directly applicable to a particular evaluation.

---

## 📄 Report Generation

Evaluation results can be exported in two formats:

### PDF Report

The PDF report contains:

- Dataset information
- Evaluation configuration
- Evaluated algorithms
- Per-algorithm metrics
- Evaluation summary

### CSV Report

The CSV export contains the stored evaluation metrics in a structured tabular format.

Exported results are validated against the results displayed in the application to ensure consistency.

CSV formula-injection protection is applied to exported values where required.

---

## 🕘 Evaluation History

Authenticated users can maintain a history of their evaluation runs.

The history functionality provides:

- Storage of completed evaluations
- Retrieval of previous evaluations
- User-specific evaluation history
- Newest-first history listing
- Deletion of owned evaluation records
- Protection against cross-user access

A user's evaluation history must not expose another user's datasets or results.

---

## 🔄 System Workflow

```text
┌─────────────────────┐
│   User / Guest      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Dataset Upload    │
│     & Validation    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Dataset Preview &   │
│ Configuration       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Evaluation Engine  │
│                     │
│ Logistic Regression │
│ Decision Tree       │
│ Random Forest       │
│ SVM                 │
│ KNN                 │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Metrics & Evaluation│
│ Results             │
└──────────┬──────────┘
           │
      ┌────┴─────┐
      ▼          ▼
┌──────────┐ ┌──────────────┐
│Visualize │ │Report Export │
│ Results  │ │ PDF / CSV    │
└──────────┘ └──────────────┘
      │          │
      └────┬─────┘
           ▼
┌─────────────────────┐
│ Evaluation History  │
│   for Users         │
└─────────────────────┘
```

---

## 🏗️ System Architecture

The system is organized into modular components responsible for different stages of the evaluation workflow.

```text
                    ┌──────────────────────┐
                    │      Frontend        │
                    │                      │
                    │ Authentication       │
                    │ Dataset Upload       │
                    │ Configuration        │
                    │ Results              │
                    │ Visualization        │
                    │ History              │
                    └──────────┬───────────┘
                               │
                               │ API
                               ▼
                    ┌──────────────────────┐
                    │       Backend        │
                    │                      │
                    │ Authentication       │
                    │ Validation           │
                    │ Configuration        │
                    │ Evaluation           │
                    │ Metrics              │
                    │ Reports              │
                    │ History              │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────────┐        ┌──────────────────┐
       │ ML Evaluation    │        │    Database      │
       │ Engine           │        │                  │
       │                  │        │ Users            │
       │ scikit-learn     │        │ Evaluation Runs  │
       │ Algorithms       │        │ Results          │
       └──────────────────┘        │ History          │
                                   └──────────────────┘
```

The detailed architecture and design are documented in the project's **Software Architecture / Design Specification (SAD)**.

---

## 🧰 Technology Stack

### Backend

- Python 3.11+
- FastAPI or Flask, according to the finalized implementation
- pandas
- NumPy
- scikit-learn

### Database

- SQLite for development and CI
- PostgreSQL for staging and deployment

### Testing

- pytest
- pytest-cov
- FastAPI/Flask test client
- Playwright or Selenium
- Locust or k6
- OWASP ZAP
- Manual security testing

### Frontend

The frontend technology follows the finalized implementation specified by the project architecture.

---

## 📁 Project Structure

```text
web-based-ml-model-evaluator/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── validation/
│   │   ├── evaluation/
│   │   ├── metrics/
│   │   ├── reports/
│   │   └── history/
│   │
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
│   ├── Team-14_SAD_Web_Based_ML_Model_Evaluator.pdf
│   ├── Team-14_SRS_Web_Based_ML_Model_Evaluator.pdf
│   └── Team-14_Test_Plan_Web_Based_ML_Model_Evaluator.pdf
│
├── test-data/
│   ├── D1-iris.csv
│   ├── D2-breast-cancer.csv
│   └── ...
│
├── .gitignore
└── README.md
```

---

## 🚀 Installation and Setup

### Prerequisites

The project requires:

- Python 3.11+
- Node.js and npm
- Git
- SQLite for development or PostgreSQL for deployment

### Clone the Repository

```bash
git clone https://github.com/<GITHUB-USERNAME>/web-based-ml-model-evaluator.git
cd web-based-ml-model-evaluator
```

### Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

#### Windows

```powershell
.venv\Scripts\activate
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Start the backend using the command defined by the finalized backend implementation.

For a FastAPI implementation:

```bash
uvicorn app.main:app --reload
```

### Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the frontend development server:

```bash
npm run dev
```

---

## 🧪 Testing

The project includes testing at multiple levels to verify functional and non-functional requirements.

### Testing Levels

| Testing Level | Purpose |
|---|---|
| Unit Testing | Validate individual modules and functions |
| Integration Testing | Validate interaction between backend components |
| API Testing | Validate endpoints, status codes, and response structures |
| System / E2E Testing | Validate the complete user workflow |
| Performance Testing | Validate evaluation performance |
| Concurrency Testing | Validate simultaneous evaluation requests |
| Security Testing | Validate authentication, authorization, input handling, and security controls |

### Run Tests

From the backend directory:

```bash
pytest
```

### Generate Coverage

```bash
pytest --cov
```

---

## 🧪 Test Data

The project test plan defines the following test datasets and inputs:

| ID | Dataset / Input | Purpose |
|---|---|---|
| D1 | Iris — 150 rows, multiclass | Multiclass metric validation |
| D2 | Breast Cancer Wisconsin — binary | Binary metrics and ROC-AUC |
| D3 | Synthetic 10,000 × 50 dataset | Performance testing |
| D4 | CSV with missing numeric values | Missing-value handling |
| D5 | CSV with categorical features/target | Categorical-data handling |
| D6 | ~10 MB file and 10 MB + 1 byte | File-size boundary testing |
| D7 | Non-CSV files renamed as `.csv` | Upload security |
| D8 | Empty, header-only, ragged, and duplicate-header CSVs | Malformed CSV handling |
| D9 | CSV containing formula-injection cells | Export security |
| D10 | Single-class target / tiny classes | Evaluation edge cases |

---

## 🔒 Security

Security controls are incorporated throughout the application.

### Authentication and Authorization

- Passwords are stored using secure password hashing.
- Protected resources require authentication where applicable.
- User identity is derived from the authenticated session/token.
- Cross-user access to datasets and evaluation results is prevented.

### Input Security

The application validates uploaded content and user-provided values to prevent:

- Invalid file uploads
- Malformed CSV processing
- SQL injection
- Cross-site scripting
- Formula injection in exported CSV files
- Unsafe uploaded content

### API Security

The API includes controls for:

- Authentication
- Authorization
- Rate limiting
- Structured error responses
- Request identification
- Input validation
- Secure error handling

### Data Protection

The application must not expose:

- Passwords
- Authentication tokens
- Sensitive credentials
- Dataset contents through logs
- Internal stack traces to users

Temporary uploaded files are managed according to the application's retention and cleanup requirements.

---

## ⚠️ Error Handling

The application uses structured API error responses for invalid or failed requests.

The documented API error structure contains:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Description of the error",
    "request_id": "request-id"
  }
}
```

The system handles relevant HTTP error conditions including:

```text
400  Bad Request
401  Unauthorized
403  Forbidden
404  Not Found
413  Payload Too Large
415  Unsupported Media Type
422  Unprocessable Entity
429  Too Many Requests
500  Internal Server Error
503  Service Unavailable
```

Internal errors must not expose stack traces, credentials, or other sensitive information to the client.

---

## 📋 Functional Requirements Covered

The system provides functionality for:

```text
Authentication
     │
     ├── Registration
     ├── Login
     └── Logout
     
Dataset Management
     │
     ├── Upload
     ├── Validation
     └── Preview
     
Evaluation Configuration
     │
     ├── Feature Selection
     ├── Target Selection
     ├── Missing-Value Strategy
     ├── Split Ratio
     └── Algorithm Selection
     
Model Evaluation
     │
     ├── Logistic Regression
     ├── Decision Tree
     ├── Random Forest
     ├── SVM
     └── KNN
     
Results
     │
     ├── Metrics
     ├── Confusion Matrix
     ├── Comparison
     └── Ranking
     
Reports
     │
     ├── PDF
     └── CSV
     
History
     │
     ├── View Evaluations
     └── Delete Own Evaluations
```

---

## 📚 Project Documentation

The repository contains the following project documents:

### Software Requirements Specification

Contains the functional and non-functional requirements of the Web Based ML Model Evaluator.

```text
docs/Team-14_SRS_Web_Based_ML_Model_Evaluator.pdf
```

### Software Architecture / Design Specification

Contains the system architecture, components, interfaces, design decisions, and architectural constraints.

```text
docs/Team-14_SAD_Web_Based_ML_Model_Evaluator.pdf
```

### Software Test Plan

Contains the testing strategy, test environment, test data, test cases, requirements traceability, defect management, and security testing.

```text
docs/Team-14_Test_Plan_Web_Based_ML_Model_Evaluator.pdf
```

---

## 🔗 Requirements Traceability

The test plan maintains traceability between the system requirements and their corresponding test cases.

| Requirement Area | Test Coverage |
|---|---|
| Authentication | TC-001 – TC-005c |
| Dataset Upload & Validation | TC-006 – TC-009c |
| Configuration | TC-010 – TC-015a |
| Evaluation & Metrics | TC-016 – TC-019f |
| Visualization | TC-020 – TC-022a |
| Report Export | TC-023 – TC-024c |
| Evaluation History | TC-025 – TC-027b |
| Non-functional Requirements | TC-N01 – TC-N06 |
| API & Error Handling | TC-API-01 – TC-API-06 |
| Security | TC-SEC-001 – TC-SEC-010 |

---

## 📌 Project Scope

### In Scope

- User authentication
- CSV upload and validation
- Dataset preview
- Dataset configuration
- Machine learning algorithm selection
- Model evaluation
- Evaluation metrics
- Result visualization
- PDF and CSV report generation
- Evaluation history
- API error handling
- Security controls
- Performance and concurrency validation

### Out of Scope

- User-supplied pretrained models
- Distributed model training
- MLOps pipelines
- Offline operation

---

## 👥 Team

| SRN | Team Number | Name |
| ------------- | :--: | ------------------------- |
| PES2UG24CS604 | 14 | YADLA AKSHITH NAIDU |
| PES2UG24CS578 | 14 | VEDANT SRIVASTAVA |
| PES2UG24CS592 | 14 | VISHAL VIJAYKUMAR NIDONI |
| PES2UG24CS599 | 14 | VIVEK R |
