# HR Privacy Processor with AI (Local LLM Middleware)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)
![LangChain](https://img.shields.io/badge/LangChain-LCEL-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)

## 📌 Project Overview
A highly secure, locally-hosted LLM middleware API designed for enterprise Human Resources and Legal departments. This project acts as a privacy-preserving processing engine that summarizes sensitive employee documents and redacts Personally Identifiable Information (PII) using a zero-temperature AI model. 

Because inference runs entirely on local infrastructure (CPU/GPU) via Ollama, **no sensitive corporate data ever leaves the internal network**, ensuring strict compliance with data sovereignty laws and corporate privacy policies.

### Core Features
* **100% Local Inference:** Powered by Ollama (targeting efficient models like Phi-3 or Llama 3 8B).
* **AI Orchestration:** Utilizes LangChain Expression Language (LCEL) for deterministic, structured prompt pipelines.
* **Built-in Observability:** Automatically tracks and exports token generation counts, latencies, and HTTP status codes to a local CSV telemetry file.
* **API Security:** Implements FastAPI dependency injection for strict API Key authentication.
* **Hybrid Deployment:** Seamlessly transitions between a Dockerized container network and a local CPU virtual environment without altering application code.

---

## 🛠️ Tech Stack

**API & Backend Framework**
* **FastAPI**: High-performance asynchronous web framework for building the API.
* **Uvicorn**: Lightning-fast ASGI server to run the FastAPI application.
* **Pydantic**: Data validation and strict schema enforcement for incoming payloads.
* **HTTPX**: Fully asynchronous HTTP client for internal network requests.

**AI & Machine Learning**
* **Ollama**: Local AI engine that runs and serves the Large Language Models.
* **LangChain**: AI orchestration framework used for prompt templating and zero-temperature LLM pipelining.
* **Models**: Designed for local CPU efficiency (e.g. Microsoft `phi3` or Meta `llama3-8b`).

**Infrastructure & DevOps**
* **Docker & Docker Compose**: Containerization and multi-service network orchestration.
* **python-dotenv**: Environment variable management adhering to the 12-Factor App methodology.

---

## 🏗️ Architecture & SOLID Principles

This project is structured using industry-standard backend patterns, adhering strictly to the **Single Responsibility** and **DRY (Don't Repeat Yourself)** principles.

```text
HR_Privacy_Processor_with_AI/
│── .env                 # Centralized configuration variables
│── requirements.txt     # Python dependencies
│── docker-compose.yml   # Container orchestration
│── client.py            # External consumer script for batch processing
│── input_docs/          # Directory containing sample HR text files
└── app/                 # Backend Application Package
    │── __init__.py      
    │── main.py          # FastAPI HTTP Controller & Routing
    │── config.py        # Environment variable registry
    │── security.py      # Dependency-injected API Key validation
    │── schemas.py       # Pydantic data contracts
    │── telemetry.py     # File I/O logic for CSV logging
    └── llm_service.py   # LangChain AI pipeline logic
```

---

## 🚀 Getting Started (Local Native Run)

### 1. Prerequisites
* Python 3.11+
* [Ollama](https://ollama.com/) installed on your host machine.
* A downloaded Ollama model (e.g., `ollama run phi3`).

### 2. Environment Setup
Clone the repository and configure your `.env` file in the project root:
```env
MOCK_API_KEY=hr_secure_key_2026
TARGET_MODEL=phi3
OLLAMA_URL=http://localhost:11434/api/generate
TELEMETRY_LOG_DIR=logs
CLIENT_API_URL=http://localhost:8000/api/v1/hr-documents/analyze
CLIENT_INPUT_DIR=input_docs
```

### 3. Installation
Create an isolated virtual environment and install dependencies:
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Running the Application
**Start the API Server:**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Execute the Batch Processor:**
In a new terminal (with the virtual environment activated), run the client script to process the sample documents located in `input_docs/`:
```bash
python client.py
```

---

## 🐳 Docker Deployment

To run the application entirely within a containerized network (which automatically handles model pulling and networking):

```bash
docker-compose up --build
```
*Note: Docker will dynamically overwrite the `localhost` routing in the `.env` file to securely route traffic across the internal container bridge.*

---

## 📡 API Reference

### `POST /api/v1/hr-documents/analyze`

**Headers:**
* `X-API-Key`: `[Your-Secret-Key]`

**Request Payload:**
```json
{
  "department": "Human Resources",
  "task": "summarize_and_redact",
  "document_text": "Employee Sarah Jenkins (ID: 884-291) reported..."
}
```

**Response Payload:**
```json
{
  "status": "success",
  "analysis": "Date: October 12, 2025. Location: Warehouse Sector 4. Reporting Manager: [REDACTED] (Employee ID: [REDACTED]). Incident Description...",
  "telemetry": {
    "tokens_generated": 224,
    "latency_seconds": 13.89
  }
}
```

---

## 📊 Telemetry & Observability
Upon processing requests, the middleware automatically appends execution metrics to `logs/metrics.csv` for monitoring system load and AI performance.

| Timestamp | Endpoint | Latency_Sec | Tokens_Generated | HTTP_Status |
| :--- | :--- | :--- | :--- | :--- |
| 2026-07-05 12:35:10 | /api/v1/hr-documents/analyze | 26.1500 | 193 | 200 |
| 2026-07-05 12:35:24 | /api/v1/hr-documents/analyze | 13.8900 | 224 | 200 |
