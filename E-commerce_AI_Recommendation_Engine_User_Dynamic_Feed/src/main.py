import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis import asyncio as aioredis

from src.config import settings
from src.domain.schemas import UserEvent
from src.infrastructure.database.session import get_db_session
from src.infrastructure.database.repositories import PostgresProductRepository
from src.infrastructure.database.models import UserAffinity

app = FastAPI(title="E-commerce AI Feed API", version="1.0.0")

# Enable CORS for the upcoming React/Vite dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Default Vite development port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_redis():
    """Dependency to provide a Redis connection."""
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    
    try:
        yield redis
    finally:
        await redis.aclose()

@app.post("/v1/events")
async def ingest_event(event: UserEvent, redis: aioredis.Redis = Depends(get_redis)):
    """Ingests user behavioral data and pushes it to the Redis stream for the AI worker."""
    try:
        payload = event.model_dump_json()
        # Push to the stream configured in ai_worker.py
        await redis.xadd("user_events_stream", {"payload": payload})
        return {"status": "success", "message": "Event queued for AI processing."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/feed/{user_id}")
async def get_feed(user_id: str, limit: int = 20, db: AsyncSession = Depends(get_db_session)):
    """Fetches the dynamically sorted product feed based on user affinities."""
    try:
        repo = PostgresProductRepository(session=db)
        feed = await repo.get_personalized_feed(user_id=user_id, limit=limit)
        return {"user_id": user_id, "feed": feed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/affinities/{user_id}")
async def get_affinities(user_id: str, db: AsyncSession = Depends(get_db_session)):
    """Fetches the raw affinity scores for the React visual dashboard chart."""
    try:
        result = await db.execute(select(UserAffinity).where(UserAffinity.user_id == user_id))
        affinity = result.scalar_one_or_none()
        
        if not affinity:
            # Return default baseline if no behavior has been processed yet
            return {"running": 0.33, "weightlifting": 0.33, "outdoor": 0.33}
            
        return {
            "running": affinity.score_running,
            "weightlifting": affinity.score_weightlifting,
            "outdoor": affinity.score_outdoor
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))