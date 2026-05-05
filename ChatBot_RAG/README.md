# Personal Knowledge Q&A Chat Bot

A RAG (Retrieval-Augmented Generation) chatbot that answers questions from your PDF files. No hallucinations: the LLM only answers from what's in your docs.

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | [Anthropic Claude](https://anthropic.com) (`claude-sonnet-4-20250514`) | Generates grounded answers from retrieved context |
| **Embeddings** | [OpenAI](https://platform.openai.com) (`text-embedding-3-small`) or `all-MiniLM-L6-v2` via sentence-transformers | Converts text chunks and questions into vectors |
| **Vector store** | [ChromaDB](https://www.trychroma.com) | Persists embeddings and runs similarity search |
| **Document parsing** | [pypdf](https://pypdf.readthedocs.io) | Extracts text from PDF files |
| **UI** | [Streamlit](https://streamlit.io) | Chat interface with source attribution |

---

## How it works

```
┌─ Ingestion (run once) ──────────────────────────────────┐
│  docs/ → load text → chunk → embed → store in ChromaDB  │
└──────────────────────────────────────────────────────────┘

┌─ Query (per question) ───────────────────────────────────┐
│  question → embed → similarity search → top-k chunks     │
│  → build prompt → Claude → grounded answer               │
└──────────────────────────────────────────────────────────┘
```

---

## Quickstart

### 1. Add your documents

Drop any `.pdf` files into the `docs/` folder.

### 2. Ingest your documents

```bash
python ingest.py
```

This runs once (or whenever you add new docs). It creates a `chroma_db/` folder with your indexed embeddings.

### 3. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) and start asking questions.

## Limitations

- **No conversation memory** - each question is answered independently without knowledge of prior questions in the session.
- **Text only** - images and tables inside PDFs are not extracted.
- **English-optimised** - the default embedding model performs best on English text.
