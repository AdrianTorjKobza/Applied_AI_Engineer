import os
import json
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# ==========================================
# 1. THE CONFIGURATION & FALLBACK TOGGLE
# ==========================================
# Flip this to True if the Docker cluster networking fails
MOCK_MODE = True

# ==========================================
# 2. THE STATE (The Agent's Memory/Clipboard)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    vault_token: str
    auth_status: str
    infrastructure_data: dict

# ==========================================
# 3. THE NODES (The Workstations)
# ==========================================
def node_authenticate(state: AgentState) -> dict:
    """Handles Keycloak Identity and Vault Secret Retrieval."""
    print("\n[SYSTEM] Executing Node: Authentication...")
    
    if MOCK_MODE:
        print("[MOCK] Bypassing Keycloak/Vault network connections.")
        return {
            "auth_status": "Success (Mocked)",
            "vault_token": "mock-sre-token-12345"
        }
    else:
        # Real logic would go here:
        # 1. Request Keycloak JWT
        # 2. Swap JWT for Vault Token
        print("[REAL] Attempting cluster authentication...")
        # For now, if MOCK is false, we will fail safely
        return {"auth_status": "Failed - Real cluster auth pending implementation", "vault_token": None}

def node_observe(state: AgentState) -> dict:
    """Simulates querying Prometheus/Kubernetes for infrastructure state."""
    print("[SYSTEM] Executing Node: Observation (Gathering Metrics)...")
    
    if MOCK_MODE:
        mock_prom_data = {
            "checkout-service": {"status": "CrashLoopBackOff", "cpu_usage": "99%", "restarts": 14},
            "payment-gateway": {"status": "Running", "cpu_usage": "12%", "restarts": 0}
        }
        return {"infrastructure_data": mock_prom_data}
    else:
        # Real logic to query Grafana/Prometheus APIs goes here
        return {"infrastructure_data": {}}

def node_llm_think(state: AgentState) -> dict:
    """The Brain: Analyzes the data and decides what to do."""
    print("[SYSTEM] Executing Node: LLM Reasoning...")
    
    # Initialize your local Ollama model
    llm = ChatOllama(
        model="llama3", # Make sure this matches the model you pulled in Step 2!
        temperature=0,
        base_url="http://127.0.0.1:11434"
    )
    
    # We construct a system prompt giving the LLM context of its environment
    sys_prompt = f"""You are an elite Kubernetes Site Reliability Engineer (SRE) AI.
    Your authentication status is: {state.get('auth_status')}
    Current Infrastructure State from Prometheus: {json.dumps(state.get('infrastructure_data'))}
    
    Analyze the user's request and the infrastructure state. Provide a brief, professional root-cause analysis and recommended fix.
    """
    
    # Prepend the system prompt to the message history
    messages_to_send = [HumanMessage(content=sys_prompt)] + list(state['messages'])
    
    response = llm.invoke(messages_to_send)
    return {"messages": [response]}

# ==========================================
# 4. THE GRAPH (The Wiring)
# ==========================================
# Initialize the graph
workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("auth", node_authenticate)
workflow.add_node("observe", node_observe)
workflow.add_node("think", node_llm_think)

# Define the flow (Auth -> Observe -> Think -> End)
workflow.set_entry_point("auth")
workflow.add_edge("auth", "observe")
workflow.add_edge("observe", "think")
workflow.add_edge("think", END)

# Compile the application
sre_agent = workflow.compile()

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    print("==============================================")
    print(" SRE AI AGENT - INITIALIZATION SEQUENCE START ")
    print(f" OPERATING MODE: {'MOCK (Offline)' if MOCK_MODE else 'REAL (Cluster)'}")
    print("==============================================\n")
    
    user_query = "Why are customers complaining that the checkout page is timing out?"
    print(f"USER QUERY: {user_query}")
    
    # Run the graph
    initial_state = {"messages": [HumanMessage(content=user_query)]}
    final_state = sre_agent.invoke(initial_state)
    
    print("\n==============================================")
    print(" FINAL AGENT RESPONSE:")
    print("==============================================")
    print(final_state["messages"][-1].content)