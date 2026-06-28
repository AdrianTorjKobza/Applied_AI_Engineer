# AI Driven Autonomous Support Triage System

An event-driven, agentic workflow automation engine built with **LangGraph**, **FastAPI**, **PostgreSQL** (with `langgraph-checkpoint-postgres`), and **Ollama (Llama 3:8b)**. This system automates support ticket ingestion, categorizes requests, drafts responses using local Large Language Models (LLM), and implements a Human-in-the-Loop (HITL) approval mechanism for urgent or low-confidence issues.

---

## High-Level Architecture

The system uses a state machine graph to process tickets asynchronously while persisting immutable checkpoints of every step in a PostgreSQL database.

```text
                          [Webhook Event / Postman Payload]
                                         |
                                         v
                                  [FastAPI Ingestion]
                                         |
                                         v
                                  [LangGraph Engine]
                                   /     |     \
    [Billing Specialist Node] ----+      |      +----> [Technical Specialist Node]
    [General Specialist Node] -----------+      
                                         |
                                         v
                              [Evaluation/Confidence Check]
                                         |
                       +-----------------+-----------------+
            (Confidence >= 0.8)                             (Confidence < 0.8)
                       |                                     |
                       v                                     v
             [Execute Resolution]                  [Human Approval Pause]
                       |                           (Interrupt / Wait for Input)
                       v                                     |
                    [E N D]                                  v
                                                   [Apply Human Decision (y/n)]
                                                             |
                                                             v
                                                   [Execute Resolution]
                                                             |
                                                             v
                                                          [E N D]
```
---

## Tech Stack
- Orchestration: LangChain LangGraph
- API Engine: FastAPI
- LLM Backend: Ollama (running llama3:8b)
- State Persistence: PostgreSQL & psycopg
- Checkpointer: langgraph.checkpoint.postgres (Asynchronous Postgres Saver)
- Testing & Ingestion: Postman
- Observability (Optional): Langfuse

##  Installation & Prerequisites
1. Local System Dependencies:
* Install Docker & Ollama.
* Pull Llama 3 via Ollama CLI:
```bash
  ollama pull llama3:8b
```
2. Database Setup (Docker):
* Spin up a persistent local PostgreSQL instance:
```bash
docker run --name pg-triage -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=adminpassword -e POSTGRES_DB=triage_db -p 5432:5342 -d postgres:15
```
3. Virtual Environment & Dependencies:
* Clone the repository, set up a virtual environment, and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install fastapi uvicorn langgraph psycopg_pool psycopg[binary] httpx python-dotenv tenacity langfuse
```
4. Configuration File:
* Update the .env file with your Langfuse public/secret keys.

## Execution Steps
1. Start the API Server:
* Launch the FastAPI development server using Uvicorn:
```bash
uvicorn api.main:app --reload --env-file .env
```
2. Trigger the Triage Engine via Webhook:
* Open Postman or run a curl command to send a POST request to http://127.0.0.1:8000/api/v1/tickets/webhook.
* Headers:
Content-Type: application/json
```text
Body (JSON):
{
  "ticket_id": "9912",
  "source": "zendesk",
  "customer_email": "client@company.com",
  "subject": "Dispute on charging invoice",
  "description": "URGENT: There is a double billing charge dispute on my credit card."
}
```
## Expected Results & Terminal Output
* Processing & Classification:
The PowerShell/terminal window displays the incoming payload and routes it dynamically to the corresponding specialist node (e.g. Billing).
```text
📥 [WEBHOOK PAYLOAD RECEIVED FROM POSTMAN]
Ticket ID       : 9912
Source Platform : zendesk
Customer Email  : client@company.com
Subject         : Dispute on charging invoice
Description     : URGENT: There is a double billing charge dispute on my credit card.

>>> [NEW WORKFLOW TRIGGERED] Initializing thread: thread_9912 <<<

[AGENT] Analyzing ticket 9912 for classification...
[CLASSIFICATION RESULT] Assigned Category: Billing
```
* Human-in-the-Loop Interruption:
Due to keywords indicating urgency/disputes, the evaluator lowers the confidence score and triggers an interactive terminal break.
```text
[EVALUATOR] Grading draft response quality and setting confidence threshold...
[EVALUATOR RESULT] Low confidence trigger detected. Pausing for Human Review.

❗ [AWAITING HUMAN INTERVENTION] LOW CONFIDENCE/URGENT TICKET DETECTED
AI Drafted Response:
Here's a sample response: ...
------------------------------------------------------------
Accept auto-send approval? Type 'y/approve' or 'n/reject':
```

## Inspecting State History (DBeaver)
- You can inspect immutable operational checkpoints directly using DBeaver Community Edition:
1. Connect to PostgreSQL at localhost:5432 (triage_db).
2. Navigate to Schemas > public > Tables > checkpoints.
3. Right-click and execute SELECT * FROM checkpoints; to view state data.
