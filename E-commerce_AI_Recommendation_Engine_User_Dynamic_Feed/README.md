# E-Commerce Event-Driven AI Recommendation Engine

An event-driven architecture that dynamically personalizes an e-commerce product feed in real-time. By tracking user behavior (e.g. dwell time) and processing it through a local Large Language Model (LLM), the system generates behavioral affinity vectors and dynamically sorts product catalogs using database-side dot-product math.

---

## 🎯 Use Case

Traditional e-commerce feeds rely on static categories or slow, batch-processed recommendation models. This project demonstrates a **local-first, real-time personalization pipeline**:
1. A user lingers on a product (e.g. a barbell).
2. The UI dispatches an interaction event payload.
3. An AI worker intercepts the event via a Redis stream and updates the user's "Persona Matrix" (Running vs. Weightlifting vs. Outdoor).
4. The database instantly recalculates a dot-product match score for every product in the catalog.
5. The UI dynamically re-renders, pushing highly relevant items to the top of the feed.

---

## ⚙️ Tech Stack

**Frontend (Presentation Layer)**
* **React 18 & Vite:** Lightning-fast UI rendering and module bundling.
* **Tailwind CSS v4:** Utility-first styling for a sleek, dark-slate enterprise aesthetic.
* **Recharts:** Interactive data visualization for the AI Persona Matrix.

**Backend (API & Processing)**
* **Python 3 & FastAPI:** High-performance, asynchronous REST API.
* **LangChain (langchain-ollama):** Orchestrates prompts and strictly parses JSON output from the LLM.
* **Ollama (llama3):** Local, private AI inference (no external API costs or latency).

**Infrastructure & Data Layer**
* **PostgreSQL & asyncpg:** High-performance relational persistence. Handles heavy dot-product math directly in the SQL query.
* **SQLAlchemy 2.0:** Asynchronous ORM utilizing Domain-Driven Design (DDD) repository patterns.
* **Redis Streams:** Decouples API ingestion from heavy AI processing via pub/sub messaging.
* **Docker Compose:** Containerized infrastructure provisioning.

---

## High-Level Architecture

The system strictly adheres to the **Single Responsibility Principle (SRP)** and operates across four decoupled layers:

1. **Ingestion (`FastAPI -> Redis`):** The API receives a behavioral payload and instantly pushes it to a Redis Stream (`user_events_stream`), returning a `200 OK` without waiting for AI processing.
2. **Analysis (`AI Worker -> Ollama`):** A background worker consumes the stream, querying the local `llama3` model to translate human behavior into a normalized vector (e.g., 80% Weightlifting, 20% Running).
3. **Persistence (`PostgreSQL`):** The new vector is upserted into the `user_affinities` table.
4. **Query Engine (`FastAPI -> PostgreSQL`):** When the UI requests the feed, Postgres multiplies the user's affinity vector against each product's embedded category weights, sorting the catalog entirely on the database side.

---

## 📂 Folder & File Structure

```text
.
├── docker-compose.yml       # Infrastructure provisioning (Redis, Postgres)
├── requirements.txt         # Python backend dependencies
├── run_api.py               # FastAPI entry point
├── scripts/
│   ├── mock_generator.py    # CLI tool to simulate concurrent user traffic
│   ├── seed_db.py           # Initializes tables and populates dummy products
│   └── verify_db.py         # CLI tool to verify DB state
├── src/                     # Backend Source (Domain-Driven Design)
│   ├── config.py            # Environment validation via Pydantic
│   ├── main.py              # API Routing & CORS configuration
│   ├── domain/              # Interfaces and Schemas
│   ├── infrastructure/      # DB Models, Session, and Repositories
│   └── workers/
│       └── ai_worker.py     # Background LangChain Redis consumer
└── frontend/                # React/Vite UI
    ├── postcss.config.js    # Tailwind v4 configuration
    ├── vite.config.js       # React config & API Reverse Proxy
    └── src/
        ├── App.jsx          # Main UI Layout
        ├── components/      # Atomic UI Elements (StatCards, AffinityRadar, Feed)
        ├── hooks/           # State Management (useDashboardData)
        └── services/        # API Client 
```

---

## How to Run and What to Expect

### Prerequisites
* **Docker Desktop** (for Redis and Postgres)
* **Python 3.10+**
* **Node.js 18+**
* **Ollama** installed locally

### Step 1: Start Infrastructure
Provision the database and cache layers in the background.
```bash
docker-compose up -d
```

### Step 2: Initialize Local AI
Ensure the Llama 3 model is downloaded and running on port 11434.
```bash
ollama run llama3
```
*(You can type `/bye` to exit the prompt; the Ollama background service will keep running).*

### Step 3: Setup Python Environment & Seed Database
Create a virtual environment, install dependencies, and **seed the database**. The system will fail if tables and products do not exist.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create tables and inject the product catalog
python scripts/seed_db.py
```

### Step 4: Boot the Distributed Backend
You will need **two separate terminal windows** (ensure the `venv` is activated in both). This separates the web traffic from the LangChain computation.

**Terminal 1 (The API Server):**
```bash
python run_api.py
```

**Terminal 2 (The AI Worker):**
```bash
python src/workers/ai_worker.py
```

### Step 5: Launch the Control Center UI
Open a **third terminal window**, navigate to the frontend folder, install Node modules, and start Vite.
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173` to view the Protos Personalization Matrix.

### Step 6: Execute the End-to-End Simulation
To watch the pipeline process streaming data, open a **fourth terminal window** (with `venv` activated) and fire the simulated traffic generator:
```bash
python scripts/mock_generator.py
```

### What to Expect
1. The **Mock Generator** will print logs of behavioral payloads being sent to the API.
2. The **AI Worker** terminal will intercept these events, query Llama 3, and log the calculated category affinity vectors.
3. In your **Browser**, toggling between users in the UI dropdown will display their newly updated AI matrices on the radar chart, and the catalog will dynamically re-sort to prioritize items matching their active interests.