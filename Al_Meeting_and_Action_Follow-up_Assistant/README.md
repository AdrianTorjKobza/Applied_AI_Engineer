# Local-First AI Meeting Assistant

A privacy-focused, local-first Python application that ingests meeting audio recordings, transcribes and diarizes speakers locally, synthesizes structured meeting notes via a **LangGraph Map-Reduce** workflow, automatically writes Markdown reports, and presents an unsent email draft for **Human-in-the-Loop (HITL)** approval before exporting to `.eml`.

---

## 1. Core Use Case & Philosophy

Cloud-based AI meeting assistants pose data-privacy risks for sensitive engineering, financial, or architectural discussions, while recurring token costs scale poorly for long meetings.

### Why Local-First?
* **100% Data Privacy:** Audio files, transcripts, and summaries never leave your hardware.
* **Zero Recurring Token Costs:** Powered by local open-weight LLMs via Ollama.
* **Resilient to Long Meetings:** A LangGraph Map-Reduce pipeline splits hour-long syncs into token-safe chunks, summarizing them independently before consolidating a unified report.
* **Human-in-the-Loop Control:** Meeting notes are documented automatically, but outbound follow-up emails require explicit human verification before draft `.eml` files are saved to disk.

---

## 2. Tech Stack

| Component | Technology | Primary Purpose |
| :--- | :--- | :--- |
| **Speech-to-Text & Alignment** | `whisperx` / `faster-whisper` | Fast local CPU (`int8`) transcription via CTranslate2 with word-level forced phoneme alignment. |
| **Speaker Diarization** | `pyannote.audio` (v3.1) | Distinct speaker identification (`SPEAKER_00`, `SPEAKER_01`, etc.) via Hugging Face gated models. |
| **Local LLM Engine** | **Ollama** (`llama3.1:8b-instruct-q8_0`) | Local reasoning, schema extraction, and email copywriting. Quantized Q8_0 weights for near-FP16 accuracy. |
| **Orchestration & Workflow** | **LangGraph** (`StateGraph`, `MemorySaver`) | Stateful graph execution, Map-Reduce fan-out/reduce logic, and HITL interrupt breakpoints. |
| **Schema & Validation** | **Pydantic v2** (`BaseModel`, `@field_validator`) | Strict structured JSON extraction enforced via Ollama's native JSON schema parsing. |
| **CLI & User Experience** | `typer`, `rich` | Terminal UI panels, progress reporting, and interactive approval prompts. |
| **File Exporters** | Native Python `email.message`, Markdown writer | Produces standard `.md` summary files and RFC-compliant `.eml` MIME unsent drafts (Outlook / Thunderbird ready). |

---

## 3. High-Level Architecture & Graph Topology

The application is modeled as a LangGraph state machine. It separates automated artifact creation (Markdown report) from sensitive outbound actions (email draft generation), halting execution at an explicit interrupt edge (`interrupt_before=["write_eml_node"]`).

```text
                       [ Input Audio File (.wav / .mp3) ]
                                      │
                                      ▼
                     [ Ingestion & Diarization Engine ]
                  (WhisperX + Pyannote -> Diarized Turns)
                                      │
                                      ▼
                        [ Chunk Transcript Node ]
                  (Split into ~2,800-token Turn Clusters)
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
             [ Map Node 1 ]                       [ Map Node N ]
            (Parallel Ollama Extraction of Partial MeetingRecords)
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                         [ Reduce Synthesize Node ]
                   (Deduplicate Actions, Merge Key Decisions)
                                      │
                                      ▼
                      [ AUTOMATED: Write Markdown Node ]
                      Writes: YYYYMMDD_HHMM_Meeting_Title.md
                                      │
                                      ▼
                          [ Draft Email Content ]
                 (Prepares Subject, Recipients, Body Payload)
                                      │
                                      ▼
                       ═════ [ HITL INTERRUPT ] ═════
                      (CLI interactive user prompt: Y/N)
                                      │
                       ┌──────────────┴──────────────┐
                       ▼ (Approved: Y)               ▼ (Rejected: N)
           [ CONDITIONAL: Write .eml ]        [ Discard & Halt ]
         Writes: YYYYMMDD_HHMM_Title.eml       (No email file created)
```

---

## 4. Folder & File Structure

```text
local_meeting_assistant/
│
├── config/
│   ├── __init__.py
│   ├── settings.py                # Environment parameters, paths, CPU compute flags, Ollama URL
│   └── prompts.py                 # Centralized system prompts for Map, Reduce, and Email drafting
│
├── data/                          # Git-ignored local storage directory
│   ├── input_audio/               # Incoming raw audio files (.wav, .mp3, .m4a)
│   ├── transcripts/               # Saved intermediate speaker-labeled plaintext transcripts
│   └── outputs/                   # Generated .md reports and .eml draft files
│
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── audio_utils.py         # File validation and HH:MM:SS timestamp formatting
│   │   └── diarization.py         # Memory-managed WhisperX + Pyannote transcription wrapper
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── schemas.py             # Pydantic v2 models (TranscriptTurn, ActionItem, MeetingRecord)
│   │   └── ollama_client.py       # LangChain ChatOllama wrapper with structured JSON extraction
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py               # MeetingState TypedDict definition
│   │   ├── nodes.py               # Core graph node functions (chunk, map, reduce, export, draft)
│   │   └── workflow.py            # LangGraph StateGraph compilation and HITL interrupt binding
│   │
│   └── exporters/
│       ├── __init__.py
│       ├── markdown_writer.py     # Deterministic Markdown file renderer
│       └── email_writer.py        # MIME .eml generator with Outlook X-Unsent: 1 header support
│
├── tests/
│   ├── __init__.py
│   ├── test_schemas.py            # Unit tests for Pydantic validators and default fallbacks
│   ├── test_exporters.py          # Integration tests for .md and .eml MIME file generation
│   └── test_workflow.py           # Offline unit tests for chunking logic and HITL interrupt edges
│
├── main.py                        # Typer CLI entry point and interactive Rich console UX
├── pyproject.toml                 # Project metadata, dev tools, and dependencies
├── requirements.txt               # Alternate pip dependencies file
└── README.md                      # Project documentation
```

---

## 5. Prerequisites & Setup Instructions

### 1. System Dependencies (FFmpeg)
WhisperX requires **FFmpeg** to decode and resample audio streams. On Windows 10/11, install via Windows Package Manager:

```powershell
winget install --id Gyan.FFmpeg -e
```
> **CRITICAL:** Close and restart your PowerShell terminal after installation so Windows reloads system `PATH` variables. Verify by running `ffmpeg -version`.

---

### 2. Ollama Setup
Ensure your local Ollama background service is running, then pull your target LLM weights:

```powershell
ollama pull llama3.1:8b-instruct-q8_0
```

---

### 3. Hugging Face Access Token (For Pyannote Speaker Diarization)
Pyannote 3.1 is a gated research model. You must accept the user terms once per account:
1. Log in at [huggingface.co](https://huggingface.co).
2. Accept User Conditions on both model pages:
   * [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   * [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
3. Go to **Settings -> Access Tokens** and create a **Read** token.
4. Set the environment variable in your PowerShell session:
   ```powershell
   $env:HF_TOKEN="hf_your_actual_token_here"
   ```

---

### 4. Virtual Environment & Python Installation
Create a clean Python 3.10+ virtual environment and install dependencies:

```powershell
# Create & activate environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install PyTorch for CPU (prevents downloading multi-GB NVIDIA CUDA binaries on non-GPU systems)
pip install torch torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# Install project and testing tools in editable mode
pip install -e ".[dev]"
```

---

## 6. Step-by-Step Execution Guide

### 1. Place your Audio Recording
Copy any supported audio file (`.wav`, `.mp3`, `.m4a`, `.flac`) into `data/input_audio/`:
```text
data/input_audio/sample_meeting.mp3
```

### 2. Execute the CLI Command
Run `main.py`, providing the relative path to the audio file and a human-readable `--title`:

```powershell
python main.py --audio data/input_audio/sample_meeting.mp3 --title "Q3 Architecture Planning"
```

### 3. Review the Automated Markdown Export
As soon as the Map-Reduce pipeline finishes synthesis, the CLI automatically writes the Markdown summary and displays a notification:
```text
[bold green]Meeting Record Automatically Written![/bold green]
File: data/outputs/YYYYMMDD_HHMM_Q3_Architecture_Planning.md
```

### 4. Human-in-the-Loop Email Approval
The pipeline **pauses execution** at the LangGraph interrupt breakpoint and displays the proposed email draft:
```text
Subject: Follow-up: Q3 Architecture Planning
Recipients: ALEX, SARAH, SPEAKER_00

Body Preview:
Here are the notes and agreed action items from today's Architecture Planning sync...
```
You will be prompted:
```text
Do you approve this email draft to generate a local .eml file? [Y/n]: 
```
* **Type `Y`:** LangGraph resumes from its memory checkpoint, generates the unsent `.eml` draft file, and saves it to `data/outputs/`.
* **Type `N`:** Execution terminates immediately without creating an email draft file.

---

## 7. Output Artifact Specification

All output files are saved to `data/outputs/` using the strict naming convention `YYYYMMDD_HHMM_sanitized_title.*`:

### 1. Markdown Summary (`.md`)
Includes structured tables and checklists generated directly from Pydantic schemas:
```markdown
# Q3 Architecture Planning
**Date:** 20260806 | **Generated via Local Ollama Meeting Assistant**

## Summary
Executive synthesis of main architectural discussions...

## Key Decisions
- Standardize on SQLite for local state persistence.
- Adopt Llama 3.1 8B Q8_0 for local extraction.

## Actions
| Assignee | Action Item | Deadline |
| :--- | :--- | :--- |
| **SPEAKER_01 (Alex)** | Benchmark WhisperX CPU inference speed | 2026-08-10 |
| **SPEAKER_00 (Sarah)** | Prepare distribution list | Not specified |

## Next Steps
- Review benchmark metrics next Tuesday.
```

### 2. Unsent Email Draft (`.eml`)
The `.eml` file embeds the custom MIME header `X-Unsent: 1`. 
* **Windows Integration:** Double-clicking the file in Windows Explorer opens it automatically in **Microsoft Outlook** or **Mozilla Thunderbird** as an **unsent draft**.
* You can manually adjust recipient email addresses or edit body text before clicking **Send** in your email client.

---

## 8. Running the Test Suite

The project includes an offline unit and integration test suite using `pytest`. Tests run in ~2 seconds without requiring an active Ollama instance or audio files.

```powershell
# Run the complete test suite with verbose output
pytest -v
```

### What is Tested?
* **`test_schemas.py`:** Verifies Pydantic v2 validators handle empty strings or `None` values returned by smaller local LLMs without throwing runtime table-rendering errors.
* **`test_exporters.py`:** Verifies safe Windows filename sanitization, Markdown table layout, and modern `EmailMessage` MIME header formatting (`X-Unsent: 1`).
* **`test_workflow.py`:** Mocks Ollama inference to test token chunking and prove that LangGraph's checkpointer reliably halts execution at the `interrupt_before=["write_eml_node"]` edge.

---

## 9. Troubleshooting & FAQ

| Error / Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `[WinError 2] The system cannot find the file specified` | **FFmpeg** is not installed or not loaded into Windows system `PATH`. | Install via `winget install --id Gyan.FFmpeg -e` and **restart your PowerShell terminal**. |
| `DiarizationPipeline got unexpected keyword argument 'use_auth_token'` | Using newer releases of `whisperx` / `pyannote.audio` where `use_auth_token` was deprecated. | Ensure `src/ingestion/diarization.py` passes `token=self.hf_token` into `DiarizationPipeline`. |
| `AttributeError: module 'whisperx' has no attribute 'DiarizationPipeline'` | In WhisperX 3.1+, the diarization pipeline moved to a submodule. | Import via `from whisperx.diarize import DiarizationPipeline`. |
| `AttributeError: 'Message' object has no attribute 'get_content'` in tests | Legacy Python `compat32` email parser being used. | Open `.eml` files using `email.message_from_binary_file(f, policy=email.policy.default)`. |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | Windows requires Admin/Developer mode to create symlinks for cached weights. | Harmless warning. Hugging Face simply stores full file copies in cache instead of symlinks. |