# End-to-End ML Pipeline

Machine Learning pipeline for financial fraud detection.

## Features
- End-to-end ML pipeline
- Data ingestion and preprocessing
- Fraud detection model training
- Experiment tracking with MLflow
- Model evaluation
- Drift detection monitoring
- Automatic retraining trigger
- REST API serving with FastAPI
- Dockerized local deployment

---

## Tech Stack
| Category | Technology |
|---|---|
| ML Framework | PyTorch |
| Experiment Tracking | MLflow |
| API Framework | FastAPI |
| Drift Detection | Evidently AI |
| Data Processing | Pandas, NumPy |
| ML Utilities | Scikit-learn |
| Containerization | Docker, Docker Compose |
| Model Serialization | Joblib |
| Visualization | Matplotlib, Seaborn |

---

## Dataset

Download the Credit Card Fraud dataset from Kaggle:

https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Place the CSV inside:

```text
data/raw/
```
---

## Architecture

Data Ingestion
      ↓
Preprocessing
      ↓
Training
      ↓
Evaluation
      ↓
MLflow Tracking
      ↓
Drift Detection
      ↓
Retraining Trigger
      ↓
FastAPI Inference

---

## Setup and Execution
- Clone repo
- `cd ML_Pipeline_Credit_Card_Fraud_Detection
- Create Virtual Environment
- Install Dependencies: `pip install -r requirements.txt
- Run the ML pipeline: `python pipeline.py
- Start MLflow UI: `mlflow ui
- Open in browser: `http://localhost:5000
- Start FastAPI server: `uvicorn src.serving.api:app --reload
- Swagger UI: `http://localhost:8000/docs
- Health endpoint: `http://localhost:8000/health
- Running with Docker: `docker-compose up --build
- Generated reports by Evidently AI: `artifacts/reports/drift_report.html