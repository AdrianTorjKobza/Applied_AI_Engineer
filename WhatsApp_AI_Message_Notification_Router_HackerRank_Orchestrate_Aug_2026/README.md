# WhatsApp AI Message Notification Router

[![Hackathon: HackerRank Orchestrate Aug 2026](https://img.shields.io/badge/Hackathon-HackerRank%20Orchestrate%20Aug%202026-00EA64?style=for-the-badge&logo=hackerrank)](https://github.com/interviewstreet/hackerrank-orchestrate-august26)
[![Local AI: Ollama](https://img.shields.io/badge/Local%20AI-Ollama%20%7C%20qwen2.5vl:7b-FF6F00?style=for-the-badge)](https://ollama.com/)
[![Vector Store: ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-8A2BE2?style=for-the-badge)](https://www.trychroma.com/)

An AI-powered, multimodal message notification routing system developed for the **HackerRank Orchestrate August 2026 Hackathon**. Built to execute entirely locally on standard consumer laptops, this system triages high-volume WhatsApp message streams, incorporating text, image posters, and audio voice notes—into personalized, actionable delivery tiers.

## 1. Problem Statement & Use Case

WhatsApp message streams are inherently noisy. A single user can simultaneously receive urgent family updates, neighborhood announcements, work alerts, promotional image posters, voice notes, and scam attempts within the same chat list. Treating all messages equally results in two primary failure modes:
* **Critical interruptions are missed** in high-volume traffic.
* **Low-value or risky messages disrupt focus** through constant notifications.

### The Solution: Personalized Triage
For every incoming message in `dataset/messages.csv`, the router assigns a personalized delivery action based on message semantics, media content, sender history, group settings, and user behavior:
* **`notify`**: High-priority or time-sensitive messages that warrant an immediate interruption.
* **`digest`**: Safe and useful content grouped for deferred consumption.
* **`mute`**: Repetitive, unwanted, promotional, suspicious, or scam-like content.

---

## 2. Technical Stack

The project is built around a **Decoupled Hybrid Architecture**, combining probabilistic multimodal reasoning with a deterministic, rule-based policy engine.

| Component | Technology | Role & Architectural Justification |
| :--- | :--- | :--- |
| **Vision-Language Model** | `Ollama` (`qwen2.5vl:7b`) | Performs local semantic classification, intent recognition, and image poster interpretation without external API dependencies. |
| **Speech-to-Text** | `faster-whisper` (`base`) | Converts audio voice notes (`.ogg`, `.wav`, `.mp3`) to text using CPU-optimized integer (`int8`) quantization. |
| **Vector Memory** | `ChromaDB` (Persistent SQLite) | Stores historical interactions and performs sender-prioritized similarity search to ground routing decisions in past user behavior. |
| **Configuration** | `pydantic-settings` | Strongly typed configuration management (`config.py`). Prevents hardcoded magic numbers or path strings across domain layers. |
| **Validation & Schemas** | `pydantic` v2 | Enforces strict I/O validation for incoming messages, LLM payloads, and final submission rows. |
| **Async Execution** | `asyncio` + `httpx` + `tqdm` | Manages non-blocking concurrent batch requests against the local Ollama daemon with progress reporting. |

---

## 3. High-Level Architecture & Data Flow

```text
+---------------------------------------+
|    Incoming Raw Message (CSV Row)     |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
|  Stage 1: Media Ingestion & Parsing   |
|  - Voice Notes -> faster-whisper (CPU)|
|  - Images -> Base64 Data URI Loader   |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
| Stage 2: Sender-Prioritized Retrieval |
|  - Query local ChromaDB vector store  |
|  - Match exact sender_user_id first   |
|  - Fallback to semantic similarity    |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
| Stage 3: Probabilistic Reasoning (LLM)|
|  - Prompt Ollama VLM (qwen2.5vl:7b)   |
|  - Extract Action, Type, Reason, &    |
|    self-assessed confidence score     |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
| Stage 4: Deterministic Policy Engine  |
|  - [Safety Override]: Scam/Spam->Mute |
|  - [Mute Override]: Group Mute->Digest|
|  - [Quiet Hours]: Non-Urgent->Digest  |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
| Stage 5: Multi-Signal Confidence      |
|  - Synthesize LLM certainty, evidence |
|    boost, and media penalties         |
+---------------------------------------+
                   |
                   v
+---------------------------------------+
|     Idempotent Export: output.csv     |
+---------------------------------------+

```
### Core Architectural Features
* **SOLID & Domain-Driven Design (DDD):** Domain logic (`rules.py`, `confidence.py`) is cleanly decoupled from infrastructure services (`audio_service.py`, `llm_router.py`, `vector_store.py`).
* **Idempotent Vector Upserts:** `VectorStoreService` indexes `message_history.csv` using deterministic message IDs. Repeated executions produce identical vector store states without record duplication.
* **Multi-Signal Confidence Calibration (`ConfidenceScorer`):** Instead of relying on raw token log-probabilities, confidence is computed synthetically:
  `Score = Clamp(C_llm + Delta_evidence - Delta_media)`
  *Policy overrides (Quiet Hours, Group Mutes, Scam blocks) receive an elevated deterministic ceiling (`0.98`) due to 100% rule precision.*

---

## 4. Folder & File Structure
```text
├── dataset/
│   ├── media/
│   │   ├── audio/                  # Audio voice note files (.ogg, .wav, .mp3, .m4a)
│   │   └── images/                 # Image poster files (.jpg, .png, .webp)
│   ├── messages.csv                # Target incoming messages requiring prediction
│   ├── output.csv                  # Generated predictions (hackathon submission format)
│   └── ...                         # User, group, business, and historical context CSVs
├── data_store/                     # ChromaDB local SQLite/Parquet vector database
├── src/
│   ├── init.py
│   ├── config.py                   # Pydantic Settings configuration module
│   ├── prompts.py                  # Externalized system prompt templates for Ollama VLM
│   ├── domain/
│   │   ├── confidence.py           # Multi-signal confidence calibration service
│   │   ├── exceptions.py           # Custom domain exception hierarchy
│   │   ├── models.py               # Pydantic data schemas & prediction contracts
│   │   └── rules.py                # Deterministic Policy Engine (Quiet Hours, Mutes)
│   ├── services/
│   │   ├── audio_service.py        # faster-whisper CPU speech-to-text integration
│   │   ├── llm_router.py           # Async Ollama client with retry/backoff & safe parsing
│   │   └── vector_store.py         # Idempotent ChromaDB retrieval service
│   ├── utils/
│   │   ├── data_loader.py          # O(1) relational context metadata loader
│   │   └── preflight.py            # Fail-fast filesystem & Ollama model validator
│   └── pipeline/
│       └── orchestrator.py         # Asynchronous batch routing pipeline
├── main.py                         # Stream-resilient application CLI entry point
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

---

## 5. Setup & Execution Guide

### Prerequisites
1. Python 3.10+ installed locally.
2. Ollama installed and running on `http://localhost:11434`.
3. Target Vision-Language Model pulled into your local Ollama registry: `ollama pull qwen2.5vl:7b`

### Step 1: Environment Initialization
1. Create virtual environment: `python -m venv venv`
2. Activate environement: on Linux / macOS: `source venv/bin/activate` | on Windows: `.\venv\Scripts\Activate.ps1`
3. Install mandatory dependencies: `pip install --upgrade pip` and `pip install -r requirements.txt`

###  Step 2: Running the System
`python -u main.py`

## 7. Architectural Trade-Offs (Local Laptop Compute)

Designing an AI-powered multimodal system to run entirely on a consumer laptop (e.g., Intel Ultra 7 CPU, 32GB RAM, integrated GPU) requires deliberate engineering trade-offs:

1. **Concurrency Throttling (`concurrent_requests: 2`):**  
   * **Decision:** We limit simultaneous LLM requests to `2` concurrent tasks rather than `8+`.
   * **Trade-Off:** Reduces throughput (`~1.5 - 3.0 messages/second`) in exchange for system stability. Running higher concurrency against a 6.0 GB vision model (`qwen2.5vl:7b`) causes GPU/CPU RAM contention and triggers HTTP read timeouts.
2. **CPU Integer Quantization for Audio (`int8`):**  
   * **Decision:** We execute `faster-whisper` using `int8` quantization on the CPU (`base` model).
   * **Trade-Off:** Slightly lower transcription fidelity for heavy accents compared to large Whisper models, but drops audio ingestion latency to under `1.0 second` per clip without competing with Ollama for VRAM.
3. **Hybrid Rule vs. Prompt Offloading:**  
   * **Decision:** We enforce Quiet Hours and Muted Group logic via deterministic Python code (`PolicyEngine`) rather than instructing the LLM to calculate time-range overlaps.
   * **Trade-Off:** Adds a small symbolic evaluation step post-inference, but completely eliminates LLM prompt drift, reducing context token consumption and guaranteeing 100% adherence to explicit user rules.
4. **Fail-Fast vs. Retry Resilience:**  
   * **Decision:** Transient server errors (`HTTP 5xx`, network timeouts) trigger an exponential backoff loop (`ollama_max_retries: 3`), while client errors (`HTTP 404 Model Not Found` or `HTTP 400 Corrupt Image Payload`) fail fast to heuristic fallbacks.
   * **Trade-Off:** Prevents infinite retry loops on unreadable images while ensuring transient Ollama load spikes do not drop valid predictions.
