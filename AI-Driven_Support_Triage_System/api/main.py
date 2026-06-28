import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

from api.schemas import WebhookPayload, WebhookResponse
from graph.workflow import workflow

app = FastAPI(title="Autonomous Support Triage Engine")
DB_URI = "postgresql://admin:adminpassword@localhost:5432/triage_db"

class ReviewActionPayload(BaseModel):
    action: str

async def get_compiled_graph(pool):
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["human_approval"])

@app.post("/api/v1/tickets/webhook", response_model=WebhookResponse)
async def ingest_webhook(payload: WebhookPayload):
    thread_id = f"thread_{payload.ticket_id}"
    initial_state = {
        "thread_id": thread_id,
        "ticket_id": payload.ticket_id,
        "description": payload.description,
        "status": "processing"
    }
    
    print("\n" + "=" * 90)
    print("📥 [WEBHOOK PAYLOAD RECEIVED FROM POSTMAN]")
    print(f"Ticket ID       : {payload.ticket_id}")
    print(f"Source Platform : {payload.source}")
    print(f"Customer Email  : {payload.customer_email}")
    print(f"Subject         : {payload.subject}")
    print(f"Description     : {payload.description}")
    print("=" * 90)
    
    print(f"\n>>> [NEW WORKFLOW TRIGGERED] Initializing thread: {thread_id} <<<")
    
    async with AsyncConnectionPool(DB_URI, kwargs={"autocommit": True}) as pool:
        compiled_graph = await get_compiled_graph(pool)
        config = {"configurable": {"thread_id": thread_id}}
        
        # 1. First execution stream (runs up to human_approval breakpoint)
        async for event in compiled_graph.astream(initial_state, config=config):
            pass
            
        current_state = await compiled_graph.aget_state(config)
        
        # 2. Catch the interruption breakpoint
        if current_state.next:
            print("\n" + "#" * 60)
            print("❗ [AWAITING HUMAN INTERVENTION] LOW CONFIDENCE/URGENT TICKET DETECTED")
            print("AI Drafted Response:")
            print(current_state.values.get("draft_response", "No draft found."))
            print("-" * 60)
            
            user_input = ""
            while user_input.lower() not in ["y", "n", "approve", "reject"]:
                user_input = input("Accept auto-send approval? Type 'y/approve' or 'n/reject': ").strip().lower()
            
            action_resolved = "approve" if user_input in ["y", "approve"] else "reject"
            new_status = "resolved" if action_resolved == "approve" else "escalated"
            
            # Commit the decision AND explicitly set the status so the node doesn't have to guess
            await compiled_graph.aupdate_state(
                config, 
                {
                    "human_action": action_resolved,
                    "status": new_status
                }, 
                as_node="human_approval"
            )

            print(f"\n[RESUMING WORKFLOW] Applying human decision: '{action_resolved}' (Status: {new_status})...")
            
            # 3. Resume the graph execution natively
            async for event in compiled_graph.astream(None, config=config):
                pass
            print("#" * 60 + "\n")

    return WebhookResponse(status="success_resolved", thread_id=thread_id)