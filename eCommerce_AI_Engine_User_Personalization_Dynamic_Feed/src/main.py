import json
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.domain.schemas import UserEvent
from src.infrastructure.database.session import get_db_session, engine
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories import PostgresProductRepository

redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    await redis_client.close()

app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

@app.post("/v1/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(event: UserEvent):
    event_dict = event.model_dump(mode='json')
    await redis_client.xadd(
        name="user_events_stream",
        fields={"payload": json.dumps(event_dict)}
    )
    return {"status": "accepted", "message": "Event queued for AI processing."}

@app.get("/v1/recommendations/homepage/{user_id}")
async def get_homepage_feed(user_id: str, db: AsyncSession = Depends(get_db_session)):
    repo = PostgresProductRepository(session=db)
    feed = await repo.get_personalized_feed(user_id=user_id)
    return {"user_id": user_id, "recommended_feed": feed}


if __name__ == "__main__":
    # This block only triggers if you run the file directly.
    # It bypasses the Uvicorn CLI string-parsing entirely.
    uvicorn.run(app, host="0.0.0.0", port=8000)