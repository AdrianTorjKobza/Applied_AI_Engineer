# AI Travel Planner (Resilient Agent)
A travel planning system built with **CrewAI** and **Ollama**. This agent is designed to handle "Tool Failures" by utilizing a multi-tool fallback strategy.

## Features
- **Local Inference:** Runs on Ollama (Llama3).
- **Real-time Data:** Uses Serper.dev for live Google Flight and Weather data.
- **Resilient Logic:** If the Google Search API fails (Rate limits/Key issues), the agent automatically pivots to DuckDuckGo.
- **Structured Output:** Outputs a clean, valid JSON itinerary via Pydantic.

## Tech Stack
- **Orchestration Framework:** [CrewAI](https://www.crewai.com/) (Role-based multi-agent collaboration).
- **Local LLM Runner:** [Ollama](https://ollama.com/) (Running Llama 3).
- **Primary Search API:** [Serper.dev](https://serper.dev/) (Google Search Results).
- **Fallback Search Tool:** [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) (Redundancy tool) & [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) (Scraping-based redundancy)[cite: 1].
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/) (For structured JSON output).

## Setup
1. **Ollama:** Install [Ollama](https://ollama.com) and run `ollama pull llama3`
2. **API Key:** Get a free API key from [Serper.dev](https://serper.dev)
3. **Environment:** Create a `.env` file and add `SERPER_API_KEY=your_key`
4. **Create a virtual environment:** `python -m venv venv`
- On Linux/MacOs use `source venv/bin/activate`
- On Windows use `venv\Scripts\activate`
5. **Install:** `pip install -r requirements.txt`
6. **Run:** `python main.py`
