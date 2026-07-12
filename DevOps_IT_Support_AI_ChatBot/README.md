# 📟 DevOps & IT System AI Troubleshooter

An enterprise-grade, local-first log parsing and streaming analytical ecosystem. This application allows DevOps professionals and IT engineers to securely isolate troubleshooting workspaces, stream high-volume crash dumps or configuration anomalies to a local LLM (`llama3`), track system metrics via GraphQL telemetry endpoints, and automatically enforce rate limits via Redis.

---

## 🎯 Use Case

When infrastructure goes down, engineers are flooded with multi-layer stack traces, obscure database connection faults, or system metrics anomalies. Copy-pasting sensitive proprietary logs into public cloud LLMs presents severe compliance risks. 

This project provides a **100% local, self-contained AI-powered terminal** that:
* **Ingests raw, unstructured logs** (e.g., connection pool exhaustion tracebacks, HTTP 500 errors).
* **Streams immediate architectural remedies** from a locally deployed `llama3` model using Server-Sent Events (SSE).
* **Enforces developer rate limits** to ensure fair resource allocation on local host hardware.
* **Provides a clear telemetry auditing layer** using a cached GraphQL API to track analytics, interaction volume, and error timelines without overloading the main database.

---

## 🛠️ Tech Stack

| Layer | Technology Component | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit (v1.32.0) | Interactive reactive UI, streaming markdown renderer, multi-tab layout, and built-in analytical data visualization using Pandas. |
| **Backend Core API** | FastAPI (v0.103.1) | Asynchronous, high-performance web framework utilizing structured dependency injection and lifespan event handlers. |
| **Streaming Pipeline**| `sse-starlette` & `httpx` | Direct async token piping via Server-Sent Events (SSE) from the model engine to the client layer without HTTP request dropouts. |
| **Local LLM Engine** | Ollama (`llama3`) | Open-source neural network execution environment running offline on local hardware compute pools. |
| **Caching & Security**| Redis (v5.0.0) | Memory-grid atomic key counters for sliding-window rate limiting and microsecond-latency GraphQL data serialization. |
| **Relational Database**| SQLAlchemy & SQLite | Structural database layer with asynchronous engine capabilities tracking historical chats and workspace schemas. |
| **Query Engine** | Strawberry GraphQL | Declarative code-first GraphQL server schema for high-precision metric collection. |

---

## 📐 High-Level Architecture

The system coordinates interactions across three isolated network-boundary tiers:

```text
                  +-----------------------------------+
                  |         Streamlit UI              |
                  |  - Error Analysis Terminal        |
                  |  - GraphQL Analytics Dashboard    |
                  +-----------------+-----------------+
                                    |
                    HTTP / SSE (8000)|
                                    v
                  +-----------------+-----------------+
                  |         FastAPI Backend           |
                  |  - Rate-limiting Interceptor      |
                  |  - REST & GraphQL Orchestrator    |
                  +----+------------+------------+----+
                       |            |            |
         Cache / Limit |            | SQL Engine | Ollama API
         (Port 6379)   v            v            v (Port 11434)
              +--------+---+   +----+----+   +---+--------+
              | Redis Grid |   | SQLite  |   | Local LLM  |
              |            |   | DB      |   | (Llama3)   |
              +------------+   +---------+   +------------+
```

1.  **Ingestion Request:** The frontend authenticates a developer session token and targets the backend streaming endpoint.
2.  **Interception (Redis):** The API evaluates incoming IP/Session hashes against an atomic sliding-window time slice counter in Redis. Excess traffic throws an automated HTTP 429 payload.
3.  **Model Stream Pipes (Ollama):** The application handles an asynchronous network stream from Ollama via `.aiter_lines()`, processing memory blocks in standard text chunks.
4.  **Cache Invalidation:** The completion of a stream flushes the Redis local cache key for that session, forcing the next GraphQL query to reload updated database metrics.

---

## 📁 Project Folder & File Structure

```text
IT_Support_AI_ChatBot/
├── api/
│   ├── __init__.py
│   ├── graphql_schema.py       # Defines Strawberry GraphQL Types, Queries, and Resolvers
│   └── middleware.py           # Implements the sliding-window Redis rate limiter
├── core/
│   ├── __init__.py
│   ├── config.py               # Pydantic v2 Settings config (binds environment variables)
│   └── redis_client.py         # Redis cluster client pooling configurations
├── db/
│   ├── __init__.py
│   └── database.py             # SQLAlchemy models, sessions, and SQLite schema mappings
├── services/
│   ├── __init__.py
│   └── ollama_service.py       # Non-blocking Async HTTP client streaming from local Ollama
├── .env                        # Environment variable configurations (Git ignored)
├── frontend.py                 # Multi-tab Streamlit dashboard interface
├── main.py                     # Central FastAPI application mount point and router map
└── requirements.txt            # Explicitly pinned project dependencies
```

---

## 🚀 How to Execute Project and What to Expect

### Prerequisites
* Python 3.11+ installed.
* Redis server running locally on `localhost:6379`.
* Ollama application installed, running, and the `llama3` model pulled (`ollama pull llama3`).

### 1. Setup the Virtual Environment and Dependencies
Open PowerShell/Terminal in the project root directory:

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root folder:
```ini
ENV=development
SQLITE_URL=sqlite:///./devops_troubleshooter.db
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SEC=60
GRAPHQL_CACHE_TTL_SEC=300
BACKEND_URL=http://localhost:8000
```

### 3. Launch the App Elements
You will need two separate terminal windows with active environments:

**Terminal 1: Start the FastAPI Backend Application Engine**
```powershell
uvicorn main:app --reload --port 8000
```
*Expected Logs:*
```text
INFO:     Started reloader process [42960] using StatReload
INFO:     Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000) (Press CTRL+C to quit)
```

**Terminal 2: Start the Streamlit Frontend GUI Application**
```powershell
streamlit run frontend.py
```

---

### What to Expect upon Execution

#### Tab 1: Error Analysis Terminal
* Upon clicking **"Initialize Workspace Connection"**, the application synchronizes with the workspace schema backend database. 
* Clicking **"Analyze Logs with Llama3"** sends the default SQLAlchemy timeout stack trace to the backend. 
* The system dynamically streams real-time tokens to your UI, breaking down why the connection limit failed and providing structural recommendations.
* If you click the button rapidly more than 20 times in a single minute, the system cuts off your connection with a clear notification: `Rate Limit Breached! (Redis Counter Intercepted Excess Requests)`.

#### Tab 2: Query Log Analytics (GraphQL)
* Clicking **"Execute GraphQL Fetch Request"** calls the Strawberry server.
* The data is passed to Pandas DataFrames and loaded into localized timeline line charts and frequency bar graphs showing usage patterns, alongside a searchable tabular grid displaying your raw communication logs.

---

## 📈 Future Potential Improvements

> * **Vectorized RAG Subsystems (Retrieval-Augmented Generation):** Integrate a local vector database (such as ChromaDB or Qdrant) to ingest internal runbooks, infrastructure documentation, and architectural markdown structures so Llama3 can cross-reference internal playbooks alongside raw log analysis.
> * **OAuth2 OIDC Authentication Integration:** Transition the lightweight "Developer Workspace Token" concept into a production-hardened identity management flow via Keycloak or Okta.
> * **Log Agent Direct Pipeline Connections:** Open an additional vector ingestion port supporting direct inputs from log aggregators like FluentBit, Logstash, or Datadog webhooks for automated alerting rather than purely manual copy-paste operations.