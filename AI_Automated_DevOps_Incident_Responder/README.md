# AI Automated DevOps Incident Responder

An intelligent, locally-hosted AI agent built to ingest infrastructure alerts, diagnose root causes via Retrieval-Augmented Generation (RAG), and formulate precise remediation strategies. Designed to run completely offline within a Kubernetes cluster using local LLMs.

---

## Overview & Use Case

**The Problem:** Modern DevOps teams are flooded with alerts from monitoring tools (Datadog, PagerDuty, Prometheus). Triage requires a human engineer to read the alert, search for logs, cross-reference internal documentation (runbooks), and formulate a fix.

**The Solution:** This project deploys an autonomous AI responder into the Kubernetes cluster. When an alert triggers a webhook:
1. **Ingestion:** A FastAPI endpoint receives the incident payload.
2. **Investigation:** A LangGraph-powered AI agent analyzes the alert.
3. **Retrieval (RAG):** The agent physically reads local service logs and searches an internal ChromaDB vector database for the correct standard operating procedure (Runbook).
4. **Remediation:** The agent outputs a structured JSON diagnosis and a step-by-step action plan (e.g., `kubectl scale` commands) to resolve the incident.

*Primary Test Scenario:* Database Connection Pool Exhaustion on a PostgreSQL Primary node.

---

## Architecture

This application operates on a containerized AI stack, utilizing a ReAct (Reasoning and Acting) agent loop:

1. **API Gateway:** `FastAPI` handles webhook ingestion and Pydantic schema validation.
2. **Agent Router:** `LangGraph` orchestrates the cognitive loop, deciding when the LLM should think, when it should use a tool, and when it should output the final answer.
3. **LLM Engine:** `Ollama` (running `llama3`) provides the inference engine. It runs locally on the host machine and is exposed to the virtual Kubernetes network via host routing.
4. **Vector Database:** `ChromaDB` generates and stores in-memory vector embeddings of internal engineering runbooks for semantic search.
5. **Observability:** `Langfuse` provides deep telemetry, tracing LLM token usage, latency, and reasoning pathways.
6. **Infrastructure:** Hosted locally via `Docker Desktop Kubernetes` with a CI/CD pipeline simulated by `act` (local GitHub Actions).

---

## Tech Stack

* **Framework:** FastAPI, Uvicorn
* **AI & Orchestration:** LangChain, LangGraph, LangChain-Ollama
* **Vector Store & RAG:** ChromaDB
* **LLM:** Ollama (Llama 3 / Phi-3 / Mistral)
* **Telemetry:** Langfuse
* **DevOps:** Docker, Kubernetes (Manifests & Helm), `act` (Local CI/CD)

---

## Project Structure

```text
AI_Automated_DevOps_Incident_Responder/
├── app/
│   ├── main.py              # FastAPI application, Pydantic models, and API endpoints
│   └── agent.py             # LangGraph compilation, ChromaDB logic, and LLM Tools
├── knowledge/               # (.txt) Engineering Runbooks for Vector Embeddings
├── logs/                    # (.txt) Mock service logs for agent ingestion
├── requirements.txt         # Python dependencies
├── Dockerfile               # Containerization instructions
└── README.md                # Project documentation
```

---

## Local Setup & Deployment

### 1. Configure the Local LLM (Ollama)
Because the application runs inside a Kubernetes pod, Ollama must be configured to accept external network traffic from the Docker bridge.
* Set the Windows Environment Variable: `OLLAMA_HOST=0.0.0.0`
* Restart Ollama.
* Pull your preferred model: `ollama run llama3`

### 2. Build and Deploy
Trigger the local GitHub Actions pipeline to build the Docker image, push it to the local registry, and deploy it to Kubernetes:
```bash
act --container-options "-v ${PWD}/.kube-temp/config:/root/.kube-host/config"
kubectl rollout restart deployment my-agent-deployment
kubectl get pods -w
```

### 3. Open the Network Tunnel
Punch a hole through the Kubernetes firewall to access the FastAPI application from your local browser:
```bash
kubectl port-forward deployment/my-agent-deployment 8000:8000
```

---

## Testing the Agent

1. Navigate to the Swagger UI: `http://localhost:8000/docs`
2. Locate the incident ingestion endpoint (e.g., `POST /incident`).
3. Click **Try it out** and inject the following test payload:

```json
{
  "id": "INC-20260706-9942",
  "priority": "P1",
  "message": "CRITICAL: Database Connection Pool Exhaustion in production-postgresql-primary. API Gateway is reporting a 504 Gateway Timeout spike. The primary PostgreSQL database connection pool has reached 100% capacity. Read/write latency has degraded past the 2000ms threshold. Active connections: 500/500."
}
```

4. Click **Execute**. 
5. Open your local **Langfuse Dashboard** (`http://localhost:3000`) to watch the execution trace as the agent searches ChromaDB, reads the logs, and formulates the response!

---

## Future Enhancements

* **Autonomous Execution:** Upgrade the agent from "Diagnostic" to "Remediation" by passing the Pod's internal `kubeconfig` to the Python app, allowing the LangGraph agent to autonomously execute `kubectl scale` commands.
* **Slack Integration:** Add a LangChain tool to output the agent's findings directly into a designated `#incident-response` Slack channel.
* **Cloud Migration:** Replace local `act` and `ttl.sh` with a true GitHub Actions pipeline deploying to AWS EKS or Azure AKS.
