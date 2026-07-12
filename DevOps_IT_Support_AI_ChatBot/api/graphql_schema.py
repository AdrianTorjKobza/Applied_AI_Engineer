import strawberry
import json
from typing import List
from db.database import SessionLocal, ChatMessage as DBMessage
from core.config import settings
from core.redis_client import get_redis

@strawberry.type
class ChatMessageGraph:
    """GraphQL presentation model for a historical chat entry."""
    id: int
    role: str
    content: str
    timestamp: str

@strawberry.type
class Query:
    @strawberry.field
    async def get_history(self, session_token: str) -> List[ChatMessageGraph]:
        """Fetches history with a strict Redis caching layer bypass strategy."""
        cache_key = f"graphql_cache:{session_token}"
        redis_client = await get_redis()
        
        # Check cache hit
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return [ChatMessageGraph(**msg) for msg in data]
            
        # Cache miss - hit SQLite
        with SessionLocal() as db:
            messages = db.query(DBMessage).filter(DBMessage.session_token == session_token).all()
            
            result = [
                ChatMessageGraph(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat()
                ) for msg in messages
            ]
            
        # Save back to Redis with custom TTL configuration
        serialized_data = json.dumps([{"id": m.id, "role": m.role, "content": m.content, "timestamp": m.timestamp} for m in result])
        await redis_client.setex(cache_key, settings.graphql_cache_ttl_sec, serialized_data)
        
        return result

schema = strawberry.Schema(query=Query)