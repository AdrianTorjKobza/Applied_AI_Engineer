import requests
import json
import operator
import logging
from typing import TypedDict, Annotated, Sequence
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from config import settings # Import your Pydantic settings object

# Configure simple logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SRE-Agent")

# ==========================================
# 1. THE STATE (Agent's Clipboard)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    vault_token: str
    auth_status: str
    infrastructure_data: dict

# ==========================================
# 2. THE NODES (Workstations)
# ==========================================

def node_authenticate(state: AgentState) -> dict:
    """Authenticates using settings from config.py and real Keycloak/Vault endpoints."""
    logger.info("Authenticating with Identity Provider...")
    
    # Extract secret safely from SecretStr
    client_secret = settings.client_secret.get_secret_value()
    
    try:
        # 1. Get JWT from Keycloak
        token_response = requests.post(
            f"{settings.keycloak_url}/realms/{settings.realm}/protocol/openid-connect/token",
            data={
                "client_id": settings.client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            },
            timeout=5
        )
        token_response.raise_for_status()
        jwt_token = token_response.json().get("access_token")

        # 2. Swap JWT for Vault Token
        vault_response = requests.post(
            f"{settings.vault_url}/v1/auth/jwt/login",
            json={"jwt": jwt_token, "role": "langgraph-auth-role"},
            timeout=5
        )
        vault_response.raise_for_status()
        vault_token = vault_response.json().get("auth", {}).get("client_token")
        
        return {"auth_status": "Success", "vault_token": vault_token}
    
    except Exception as e:
        logger.error(f"Authentication failure: {e}")
        return {"auth_status": f"Failed: {e}", "vault_token": "none"}

def node_observe(state: AgentState) -> dict:
    """Mocks infrastructure metrics (Hybrid mode)."""
    logger.info("Gathering Metrics (Mocked Prometheus)...")
    
    # This data represents what would come from your real Prometheus query
    mock_prom_data = {
        "checkout-service": {"status": "CrashLoopBackOff", "cpu_usage": "99%", "restarts": 14}
    }
    return {"infrastructure_data": mock_prom_data}

def node_llm_think(state: AgentState) -> dict:
    """Uses Pydantic settings to configure the LLM."""
    logger.info("Executing LLM Reasoning...")
    
    llm = ChatOllama(
        model=settings.llm_model,
        temperature=0,
        base_url=settings.ollama_base_url
    )
    
    sys_prompt = f"""You are an elite Kubernetes Site Reliability Engineer (SRE) AI.
    Your authentication status is: {state.get('auth_status')}
    Current Infrastructure State: {json.dumps(state.get('infrastructure_data'))}
    
    Analyze the user's request and the infrastructure state. Provide a brief, professional root-cause analysis and recommended fix.
    """
    
    messages_to_send = [HumanMessage(content=sys_prompt)] + list(state['messages'])
    response = llm.invoke(messages_to_send)
    return {"messages": [response]}

# ==========================================
# 3. GRAPH WIRING
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("auth", node_authenticate)
workflow.add_node("observe", node_observe)
workflow.add_node("think", node_llm_think)

workflow.set_entry_point("auth")
workflow.add_edge("auth", "observe")
workflow.add_edge("observe", "think")
workflow.add_edge("think", END)

sre_agent = workflow.compile()

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    print(f"--- SRE AI AGENT STARTING (Model: {settings.llm_model}) ---")
    
    user_query = "Why are customers complaining that the checkout page is timing out?"
    
    # Run the graph
    initial_state = {"messages": [HumanMessage(content=user_query)]}
    final_state = sre_agent.invoke(initial_state)
    
    print("\n--- FINAL AGENT RESPONSE ---")
    print(final_state["messages"][-1].content)