# Agentic AI Pipeline: Automated B2B Invoice Processing

This project implements a local Agentic AI pipeline designed to automate the processing of wholesale purchase orders. It reads natural language emails, extracts purchasing entities, and deterministically calculates the final invoice total using a modern ReAct (Reason and Act) loop via LangChain.

## The Challenge & Solution

Large Language Models (LLMs) excel at natural language processing but struggle with precise floating-point arithmetic. Asking an 8B parameter model to calculate an 18% discount on $1,720.40 frequently results in hallucinations.

**The Solution:** We decoupled the logic. The LLM (Qwen 2.5:7B) handles entity extraction and decision routing, while mathematical operations are strictly delegated to custom, deterministic Python tools. The agent uses LangChain's tool-calling framework to dynamically pass extracted arguments to these tools until the final total is achieved.

## High-Level Architecture

The pipeline consists of three core components:
1. **Deterministic Python Tools:** Three functions (`calculate_subtotal`, `apply_discount`, `calculate_final_total`) decorated as LangChain tools, equipped with explicit Pydantic type-hints and docstrings.
2. **Local Inference Engine (Ollama):** We utilize `qwen2.5:7b` running locally. Qwen 2.5 is chosen for its exceptional native tool-calling capabilities and structured output adherence.
3. **Agent Executor (LangChain):** A `agent_executor` manages the execution state. It injects a system prompt containing defaults (0% discount, $0 shipping) and forces the LLM to interact with the tools to resolve the user input.

## Tech Stack

* **Language:** Python 3.10+
* **Framework:** LangChain, LangGraph
* **Local LLM Engine:** Ollama
* **Model:** Qwen 2.5 (7B parameters)
* **Data Processing:** Pandas

## Setup & Installation

**1. Install Ollama & Pull the Model**
Ensure you have [Ollama](https://ollama.com/download) installed on your machine.
```bash
# Pull the recommended model
ollama run qwen2.5:7b
```

**2. Clone the Repository**
```bash
git clone [this repository]
cd B2B_Billing_AI_Agent_Automator
```

**3. Set Up the Python Environment**
It is recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## How to Run

Ensure your input file (`test.csv`) is formatted correctly and located in the `data` directory. The script expects `order_id` and `email_text` columns.

Run the pipeline:
```bash
python main.py
```

### **What Happens During Execution?**
1. **Data Ingestion:** Pandas loads the batch data from `test.csv`.
2. **Reasoning Loop:** For each row, the Agent reads the email text.
3. **Tool Execution:** You will see the agent's internal monologue in the console as it sequentially calls the math tools.
4. **Data Export:** The script isolates the final numerical output and appends it to a new `Total_Bill` column.
5. **Result:** A final `predictions.csv` file is generated.

## Edge Cases Handled

* **Missing Discounts:** The system prompt instructs the agent to assume a **0%** discount if none is mentioned.
* **Missing Delivery Fees:** The agent defaults to **$0** shipping.
* **Parsing Errors:** Handled gracefully via LangChain's `handle_parsing_errors=True`, which prevents pipeline crashes on erratic model outputs.
