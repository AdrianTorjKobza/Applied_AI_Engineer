# HackerRank Orchestrate Jun 2026: Multi-Modal Evidence Review System

An automated, local-first AI pipeline designed to verify damage claims across cars, laptops, and packages. This system synthesizes visual evidence (images), conversational transcripts, corporate policy requirements, and user risk histories to output deterministic claim adjudications.

This solution was developed for the [**HackerRank Orchestrate Hackathon (June 2026)**](https://www.hackerrank.com/contests/hackerrank-orchestrate-june26/challenges/multi-modal-review).


## 🧠 Architecture & Solution Strategy

Running multiple 7B+ parameter multi-modal models locally on standard developer hardware (e.g., Intel Core Ultra 7, 32GB RAM) introduces severe I/O bottlenecks. Alternating between a Vision model and a Text model per-claim causes extreme disk thrashing (loading/unloading weights from RAM) and triggers HTTP timeouts.

To achieve production-grade speed and stability, this system implements a **Model-Isolated Two-Pass Batch Architecture**:

1. **Pass 1: Vision Feature Extraction (`qwen2.5vl:7b`)**
   * The pipeline loads the Vision-Language Model (VLM) exactly once.
   * It sequentially scans all user-submitted images, extracting objective physical descriptions (objects, parts, visible damage, blurriness).
   * **Optimization:** The VLM is instructed to output *plain text* rather than strict JSON, eliminating cognitive formatting strain and preventing hallucinated fallback errors.
   * Insights are cached in local memory, and the VLM is unloaded.

2. **Pass 2: Policy Logic & Synthesis (`qwen2.5:7b`)**
   * The text-only LLM is loaded into memory exactly once.
   * It maps the cached visual insights against the historical datasets (`user_history.csv`) and regulatory limits (`evidence_requirements.csv`).
   * **Optimization:** The LLM's output schema is tightly constrained to analytical fields only (e.g., `claim_status`, `severity`, `risk_flags`). Static input context (like the long `user_claim` transcripts) is bypassed during generation to reduce token generation time from minutes to seconds per row.

## ⚡ Key Optimizations

* **Dynamic Image Compression:** Uses Python's `Pillow` (PIL) library to dynamically resize high-resolution test images to a maximum of `800x800` pixels and convert them to compressed JPEGs *before* Base64 encoding. This reduces the token payload sent to the VLM by >90%, completely eliminating context-window blowouts and 404 connection drops.
* **Proactive Runtime Monitoring:** Pass 1 includes active substring monitoring of model outputs. If the VLM fails to parse an image, it alerts the terminal immediately rather than failing silently into the final CSV.
* **Resilient Data Casting:** A schema safety net intercepts hallucinated array types from the local LLM (e.g., returning `["img_1.jpg"]` instead of `"img_1.jpg"`) and dynamically casts them to corporate-standard semicolon-delimited strings to guarantee Pydantic validation survival.

## 🛠️ Tech Stack & Requirements

* **Language:** Python 3.10+
* **Core Libraries:** `pandas` (Data pipelines), `pydantic` (Schema validation), `requests` (API connections), `Pillow` (Image optimization).
* **Local Inference Engine:** [Ollama](https://ollama.com/)
* **AI Models:** * `qwen2.5vl:7b` (Visual inspection)
  * `qwen2.5:7b` (Textual reasoning and synthesis)

## 🚀 Setup & Installation

**1. Clone the repository and navigate to the code directory:**
```bash
cd hackerrank-orchestrate-june26/code
```

**2. Initialize the Python Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**4. Pull the Local Models via Ollama:**
Ensure the Ollama service is running in the background, then pull the required weights:
```bash
ollama pull qwen2.5vl:7b
ollama pull qwen2.5:7b
```

## 📊 Execution & Usage

### 1. Evaluation & Benchmarking
To test the system against the labeled `sample_claims.csv` and generate the required Operational Analysis Report:

```bash
cd evaluation
python main.py
```
This will output `evaluation_report.md` tracking latency, accuracy, and token operational costs.

### 2. Production Run
To execute the pipeline against the unlabeled test set and generate the final output payload:

```bash
cd ..  # Return to the code/ directory
python main.py
```
The console will provide real-time textual updates for both Pass 1 and Pass 2. Upon completion, the strictly formatted `output.csv` will be generated in the root directory.

## 📁 Repository Layout
```text
.
├── AGENTS.md                         # Rules for AI coding tools + transcript logging
├── problem_statement.md              # Full task description and I/O schema
├── README.md                         # This file
├── output.csv                        # Final predictions payload
├── code/                             # Core implementation logic
│   ├── main.py                       # Production execution pipeline
│   ├── models.py                     # Pydantic schema validation boundaries
│   ├── data_loader.py                # Reference CSV ingestion engine
│   ├── vlm_agent.py                  # Pass 1 Visual Connector
│   ├── logic_agent.py                # Pass 2 Policy Synthesis Connector
│   ├── utils.py                      # PIL Image optimization utilities
│   ├── requirements.txt              # Environment dependencies
│   └── evaluation/
│       ├── main.py                   # Benchmarking and accuracy tracking engine
│       └── evaluation_report.md      # Auto-generated metrics report
└── dataset/                          # Source datasets and image files
```