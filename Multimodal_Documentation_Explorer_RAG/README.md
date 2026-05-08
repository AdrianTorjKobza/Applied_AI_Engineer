# Multimodal Documentation Explorer (RAG)

A RAG system designed for pdf documents and technical manuals. It retrieves relevant text and picture/diagrams to provide visual-contextual answers.

## Features
- **Visual Ingestion**: Uses `Moondream` via Ollama to describe diagrams.
- **Hybrid Retrieval**: Queries both text chunks and image descriptions in `Qdrant`.
- **Intelligent Response**: Uses `Llama 3.2` to synthesize answers.
- **Gradio UI**: Side-by-side view of AI explanation and retrieved source diagrams.

## Prerequisites
1. [Ollama](https://ollama.com/) installed and running.
2. Models pulled:
   ```bash
   ollama pull llama3.2
   ollama pull moondream
   
## Setup & Execution
1. Clone the repo.
2. Initialize Ollama: Ensure your local server is running ollama serve.
3. Setup Env: Create a virtual environment (`python -m venv venv`) and activate it.
4. Install dependencies: Run `pip install -r requirements.txt`.
5. Launch: Run `bash python app.py`. The first ingestion might take a while as it processes images through Moondream.

## Usage
1. Upload a PDF document or technical manual.
2. Wait for the "Ingestion Complete" status.
3. Ask a question.
4. The system will display the text answer and the most relevant picture/diagram found in the PDF.
