import os
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from app.config import settings

# --- 1. STATE SCHEMA ---
class AgentState(TypedDict):
    # This automatically appends new messages to the existing list
    messages: Annotated[list, add_messages]

# --- 2. VECTOR DB INITIALIZATION ---
_runbook_db = None

def get_runbook_db():
    global _runbook_db

    if _runbook_db is None:
        print("Initializing Local Chroma Vector DB...")
        loader = DirectoryLoader('./knowledge', glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()
        
        embeddings = OllamaEmbeddings(
            model="llama3", 
            base_url=settings.OLLAMA_BASE_URL
        )
        
        _runbook_db = Chroma.from_documents(documents, embeddings)
        print("Vector DB Initialized Successfully.")
    
    return _runbook_db

# --- 3. AGENT TOOLS ---
@tool
def fetch_cluster_logs(service_name: str) -> str:
    """Fetches recent log files for a specific service running in the cluster."""
    clean_service = service_name.strip()
    log_path = f"./logs/{clean_service}.txt"
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as file:
            return file.read()
    
    return f"Error: No physical logs found on disk for service '{clean_service}' at path {log_path}."

@tool
def query_runbook(query: str) -> str:
    """Searches the internal engineering knowledge base and runbooks for standard operating procedures."""
    try:
        db = get_runbook_db()
        results = db.similarity_search(query, k=1)
        if results:
            return results[0].page_content
        return "No relevant runbook found in the knowledge base."
    except Exception as e:
        return f"Vector DB Error: {str(e)}"

tools = [fetch_cluster_logs, query_runbook]

# --- 4. LLM & NODE LOGIC ---
llm = ChatOllama(
    model="llama3", 
    base_url=settings.OLLAMA_BASE_URL
)

# Bind the tools to the LLM so it knows it can call them
llm_with_tools = llm.bind_tools(tools)

# Define the primary thinking node
def call_model(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# --- 5. LANGGRAPH COMPILATION ---
workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Add the edges (The Routing Logic)
workflow.add_edge(START, "agent")

# 'tools_condition' checks if the LLM decided to use a tool.
# If yes, it routes to 'tools'. If no, it routes to END.
workflow.add_conditional_edges("agent", tools_condition)

# Once tools are done, always route back to the agent to evaluate the results
workflow.add_edge("tools", "agent")

# Compile the final executable graph
agent_executor = workflow.compile()