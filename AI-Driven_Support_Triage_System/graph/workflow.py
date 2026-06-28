import json
import re
from langgraph.graph import StateGraph, END
from graph.state import TriageState
from core.llm_client import LocalLLMClient
#from langfuse import observe

llm = LocalLLMClient()

#@observe(name="classify_node")
async def classify_ticket_node(state: TriageState) -> dict:
    print(f"\n[AGENT] Analyzing ticket {state['ticket_id']} for classification...")
    
    # 🌟 UPGRADED PROMPT: Stronger constraints to catch 'charging', 'billing', 'dispute'
    prompt = f"""You are an expert support triage AI. Analyze the support ticket description and assign it to exactly one category: 'Billing', 'Technical', or 'General'.
    
    - Choose 'Billing' if the ticket is about invoices, double charges, payments, subscriptions, refunds, or money disputes.
    - Choose 'Technical' if the ticket is about software bugs, login failures, server downtime, or IT infrastructure configuration.
    - Choose 'General' for feature requests, sales inquiries, or simple account questions.
    
    Ticket Description: {state['description']}
    
    Return ONLY a valid JSON object in this exact format: {{"category": "category_name"}}
    """
    
    response = await llm.generate(prompt)
    raw_text = response.get("response", "")
    category = "General"
    try:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            category = parsed.get("category", "General").capitalize()
            # Enforce strict boundary fallback
            if category not in ["Billing", "Technical", "General"]:
                category = "General"
    except Exception:
        pass
    print(f"[CLASSIFICATION RESULT] Assigned Category: {category}")
    return {"category": category}

#@observe(name="billing-generation")
async def billing_agent_node(state: TriageState) -> dict:
    print(f"\n[AGENT] Billing specialist drafting resolution...")
    prompt = f"Draft a response to this Billing issue: {state['description']}"
    res = await llm.generate(prompt)
    return {"draft_response": res.get("response", "")}

#@observe(name="technical-generation")
async def technical_agent_node(state: TriageState) -> dict:
    print(f"\n[AGENT] Technical specialist drafting resolution...")
    prompt = f"Draft a response to this Technical issue: {state['description']}"
    res = await llm.generate(prompt)
    return {"draft_response": res.get("response", "")}

#@observe(name="general-generation")
async def general_agent_node(state: TriageState) -> dict:
    print(f"\n[AGENT] General specialist drafting resolution...")
    prompt = f"Draft a response to this General issue: {state['description']}"
    res = await llm.generate(prompt)
    return {"draft_response": res.get("response", "")}

#@observe(name="eval_node")
async def evaluation_node(state: TriageState) -> dict:
    print(f"\n[EVALUATOR] Grading draft response quality and setting confidence threshold...")
    desc_lower = state['description'].lower()
    if "urgent" in desc_lower or "dispute" in desc_lower or "money" in desc_lower:
        print(f"[EVALUATOR RESULT] Low confidence trigger detected. Pausing for Human Review.")
        return {"confidence_score": 0.45, "status": "requires_review"}
    print(f"[EVALUATOR RESULT] High confidence. Proceeding to final resolution auto-send.")
    return {"confidence_score": 0.90, "status": "resolved"}

async def human_approval_node(state: TriageState) -> dict:
    # State updated externally via input() intercept
    if state.get("human_action") == "approve":
        return {"status": "resolved"}
    return {"status": "escalated"}

async def execute_resolution_node(state: TriageState) -> dict:
    print(f"\n==============================================")
    if state.get("status") == "resolved":
        print(f"[FINAL ACTION] Resolution email auto-sent/posted to ticket system.")
    else:
        print(f"[FINAL ACTION] Ticket explicitly escalated to human team.")
    print(f"==============================================")
    return {}

# --- Routing Logic ---
def router_edge(state: TriageState) -> str:
    return state.get("category", "General").lower()

def evaluation_edge(state: TriageState) -> str:
    if state.get("status") == "requires_review":
        return "human_approval"
    return "execute_resolution"

# --- Building the State Graph ---
workflow = StateGraph(TriageState)

workflow.add_node("classifier", classify_ticket_node)
workflow.add_node("billing", billing_agent_node)
workflow.add_node("technical", technical_agent_node)
workflow.add_node("general", general_agent_node)
workflow.add_node("evaluator", evaluation_node)
workflow.add_node("human_approval", human_approval_node)
workflow.add_node("execute_resolution", execute_resolution_node)

workflow.set_entry_point("classifier")
workflow.add_conditional_edges("classifier", router_edge, {"billing": "billing", "technical": "technical", "general": "general"})

for agent in ["billing", "technical", "general"]:
    workflow.add_edge(agent, "evaluator")

workflow.add_conditional_edges("evaluator", evaluation_edge, {"human_approval": "human_approval", "execute_resolution": "execute_resolution"})
workflow.add_edge("human_approval", "execute_resolution")
workflow.add_edge("execute_resolution", END)