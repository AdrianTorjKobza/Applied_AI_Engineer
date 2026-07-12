from fastapi import FastAPI, Depends, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from core.config import settings
from core.redis_client import redis_pool, get_redis
from db.database import init_db, get_db, ChatMessage as DBMessage, ChatSession as DBSession
from services.ollama_service import OllamaService
from api.middleware import verify_rate_limit
from api.graphql_schema import schema
from strawberry.fastapi import GraphQLRouter

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

ollama_service = OllamaService()

class ChatRequest(BaseModel):
    prompt: str

@app.on_event("startup")
def startup_event():
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await redis_pool.disconnect()

@app.post("/v1/session")
def create_session(x_session_token: str = Header(...), db=Depends(get_db)):
    """Registers or fetches a secure developer environment workspace token."""

    existing = db.query(DBSession).filter(DBSession.session_token == x_session_token).first()

    if not existing:
        new_session = DBSession(session_token=x_session_token)
        db.add(new_session)
        db.commit()
    
    return {"status": "session_validated"}

@app.post("/v1/chat/stream")
async def stream_chat(
    payload: ChatRequest,
    http_request: Request,
    x_session_token: str = Header(...),
    redis_client=Depends(get_redis),
    db=Depends(get_db)
):
    """Enforces rate-limits, handles data ingestion, and pipes response blocks via SSE."""
    await verify_rate_limit(http_request, redis_client)
    
    user_msg = DBMessage(session_token=x_session_token, role="user", content=payload.prompt)
    db.add(user_msg)
    db.commit()

    async def event_generator():
        try:
            full_assistant_reply = ""
            async for chunk in ollama_service.stream_chat(payload.prompt):
                full_assistant_reply += chunk
                yield {"event": "message", "data": chunk}
                
            # Only save to DB if the generation completed successfully
            with SessionLocal() as background_db:
                assistant_msg = DBMessage(session_token=x_session_token, role="assistant", content=full_assistant_reply)
                background_db.add(assistant_msg)
                background_db.commit()
                
            await redis_client.delete(f"graphql_cache:{x_session_token}")
            
        except Exception as e:
            # Send the python exception directly to the Streamlit UI
            error_msg = f"\n\n**[Backend Stream Crash]:** {str(e)}"
            yield {"event": "message", "data": error_msg}

    return EventSourceResponse(event_generator())