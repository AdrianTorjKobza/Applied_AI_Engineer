# Omnichannel AI Campaign Platform

A scalable, asynchronous platform designed to generate multi-asset marketing campaigns (Text, Images, and SEO Metadata) using Local AI (Ollama and Qwen 2.5). 

This project demonstrates enterprise-grade architectural patterns, including the **REST "202 Accepted" Background Worker Pattern** to prevent HTTP timeouts, and **GraphQL DataLoaders** to efficiently resolve deeply nested AI assets while solving the classic N+1 database query problem.

---

## The Business Use Case: Omnichannel Product Launch

Generating AI content (especially multi-modal content) is a computationally heavy and time-consuming process. A standard synchronous HTTP request would simply timeout while waiting for an LLM to write a blog post, extract SEO tags, and render an image.

**This platform solves this by orchestrating an asynchronous DAG (Directed Acyclic Graph) workflow:**
1. A marketer submits a raw product specification and target audience.
2. The platform instantly accepts the request and delegates the heavy lifting to a background queue.
3. A background worker orchestrates calls to local AI models to generate a marketing blog post, extract structured JSON SEO metadata, and generate/mock a promotional image (mock image is generated due to limitation of local environment).
4. Clients can track the job in real-time and fetch the deeply nested relational data using an optimized GraphQL graph.

---

## 🏗️ High-Level Architecture

The system is strictly decoupled into distinct functional layers, adhering to SOLID principles:

1. **Ingestion Layer (FastAPI REST):** Accepts the payload, persists an initial `PENDING` state to PostgreSQL, pushes the workload to Redis, and immediately returns a non-blocking `202 Accepted` with a Job ID.
2. **Message Broker (Redis):** Acts as the robust queuing mechanism connecting the web tier to the background workers.
3. **Processing Layer (Celery & Ollama):** Background workers consume tasks, manage state transitions (`PROCESSING`, `COMPLETED`, `FAILED`), and orchestrate external HTTP calls to the local AI Engine (Ollama).
4. **Presentation Layer (Strawberry GraphQL):** Exposes a typed graph of the finalized data. Utilizes **DataLoaders** to batch SQL queries—reducing hundreds of potential DB calls for nested assets/metadata into exactly 3 optimized queries.
5. **Client Layer (Streamlit):** A lightweight, reactive frontend that triggers jobs and polls the GraphQL endpoint to dynamically render AI assets as they complete.

---

## 💻 Tech Stack

* **Language:** Python 3.11
* **Web Framework:** FastAPI (REST Ingestion & WebSockets)
* **GraphQL Framework:** Strawberry GraphQL (with DataLoader support)
* **Background Workers:** Celery
* **Message Broker / Cache:** Redis
* **Database & ORM:** PostgreSQL + SQLAlchemy
* **Local AI Engine:** Ollama (Model: `qwen2.5:7b`)
* **Frontend UI:** Streamlit
* **Infrastructure:** Docker & Docker Compose

---

## 📂 Folder & File Structure

The project follows a modular, domain-driven structure to separate concerns:

```text
omnichannel-ai-platform/
├── docker-compose.yml         # Container orchestration (DB, Redis, Web, Worker, UI)
├── requirements.txt           # Python dependencies
├── ui.py                      # Streamlit frontend application
├── .env                       # Environment variables
├── media/                     # Shared volume for generated assets (images)
│   └── assets/                
└── app/                       # Core Backend Application
    ├── main.py                # FastAPI & GraphQL application entry point
    ├── core/                  # Infrastructure configurations
    │   ├── config.py          # Pydantic environment validation
    │   ├── database.py        # SQLAlchemy session management
    │   └── celery_app.py      # Celery instance & Redis connection
    ├── models/                # SQLAlchemy ORM Models (Jobs, Assets, Metadata)
    ├── schemas/               # Pydantic schemas (REST Payload Validation)
    ├── api/                   # REST Endpoints (Ingestion layer)
    │   └── v1/launch.py       
    ├── graphql/               # GraphQL Presentation Layer
    │   ├── schema.py          # Queries & Subscriptions
    │   ├── types.py           # Output node types
    │   └── dataloaders.py     # N+1 optimization logic
    ├── services/              # External Integrations
    │   └── ollama_client.py   # Wrapper for local LLM text/JSON extraction
    └── worker/                # Background Processing
        └── tasks.py           # Celery execution flow (State tracking + AI calls)
```

---

## 🛠️ Prerequisites & Setup

Before running the application, ensure you have the following installed:
1. **Docker & Docker Compose**
2. **Ollama:** Installed locally on your host machine to process AI prompts without cloud API costs.

**Prepare your Local AI:**
You must pull the required text model to your local machine before starting the workers:
```bash
ollama run qwen2.5:7b
```
*(Once the prompt appears, you can exit by typing `/bye`. The model is now cached and ready).*

---

## 🚀 How to Execute & What to Expect

**1. Boot the Infrastructure**
Navigate to the root directory and start the Docker Compose stack:
```bash
docker compose up --build
```
*This spins up 5 containers: Postgres, Redis, FastAPI backend, Celery worker, and Streamlit frontend.*

**2. Access the Application**
Once booted, the platform exposes several interfaces:
* **The Web UI (Streamlit):** [http://localhost:8501](http://localhost:8501)
  * *What to expect:* A clean dashboard where you can submit product specs. Watch the UI automatically poll the backend and dynamically render the text, code blocks, and mock images once the background worker finishes.
* **REST API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
  * *What to expect:* Use the `/api/v1/launch` endpoint to manually trigger the 202-Accepted pipeline and receive a raw UUID.
* **GraphQL IDE (Strawberry):** [http://localhost:8000/graphql](http://localhost:8000/graphql)
  * *What to expect:* Write deeply nested queries to fetch your campaigns. Notice the terminal logs—thanks to DataLoaders, massive nested queries only hit the database a maximum of 3 times.

---

## 🔮 Future Improvements (V2 Roadmap)

This architecture is built to scale. Future iterations could easily integrate the following enhancements:

1. **Multi-Agent Orchestration (LangGraph):** Transition the linear Celery task into a LangGraph state machine. This allows for complex feedback loops (e.g., an AI "Editor" agent reviewing the generated copy and sending it back to the "Writer" agent if the SEO score is too low).
2. **True Image Generation (Stable Diffusion):** Replace the current lightweight image mocker with an integration to a local Stable Diffusion / ComfyUI API, allowing real AI image synthesis using dedicated local GPUs.
3. **Cloud Portability:** The `OllamaService` interface can easily be swapped for OpenAI, Anthropic, or Midjourney cloud APIs by simply updating the classes in `app/services/`, leaving the core architecture untouched.
4. **Cloud Object Storage:** Transition the local `/media/` volume strategy to an AWS S3 (or local MinIO) client for distributed image serving.
