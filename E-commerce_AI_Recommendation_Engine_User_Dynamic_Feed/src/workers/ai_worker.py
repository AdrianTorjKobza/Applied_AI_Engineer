# LangChain + Redis Stream Consumer
import sys
import os

# Path Resolution: Calculate the absolute path to the project root (two levels up)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Inject the project root into Python's module search path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import json
import logging
from redis import asyncio as aioredis

# 3. Use the modernized standalone langchain-ollama package
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.config import settings
from src.domain.schemas import CategoryAffinity
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.repositories import PostgresUserAffinityRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI Components
llm = OllamaLLM(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model
)

parser = JsonOutputParser(pydantic_object=CategoryAffinity)

prompt = PromptTemplate(
    template="""
    You are an E-commerce AI profiling engine. 
    Analyze the user's recent behavior event and output their updated category affinities.
    The output MUST be a JSON object with scores between 0.0 and 1.0 summing to 1.0.
    
    User Event Context: {event_data}
    
    {format_instructions}
    """,
    input_variables=["event_data"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | llm | parser

async def process_event(message_id: str, payload: dict, redis_client: aioredis.Redis):
    """Processes a single event: Queries LLM and updates Postgres."""
    user_id = payload.get('user_id')
    logger.info(f"Processing Event: {payload.get('event_type')} for User: {user_id}")
    
    try:
        # AI Calculation (LangChain)
        new_affinities = await chain.ainvoke({"event_data": json.dumps(payload)})
        logger.info(f"Calculated Affinities for {user_id}: {new_affinities}")
        
        # Database Injection & Persistence
        async with AsyncSessionLocal() as db_session:
            repo = PostgresUserAffinityRepository(session=db_session)
            await repo.update_affinities(user_id=user_id, affinities=new_affinities)
            logger.info(f"Successfully persisted affinities for {user_id} to PostgreSQL.")
        
        # Acknowledge message in Redis
        await redis_client.xack("user_events_stream", "ai_group", message_id)
        
    except Exception as e:
        logger.error(f"Failed to process message {message_id} for user {user_id}: {e}")

async def main():
    """Main async loop polling the Redis stream."""
    logger.info("AI Worker initializing...")
    
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    
    # Ensure consumer group exists
    try:
        await redis_client.xgroup_create("user_events_stream", "ai_group", id="0", mkstream=True)
    except aioredis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise e

    logger.info("Listening to 'user_events_stream'...")

    try:
        while True:
            events = await redis_client.xreadgroup(
                groupname="ai_group", 
                consumername="worker_1", 
                streams={"user_events_stream": ">"}, 
                count=1, 
                block=2000
            )
            
            if not events:
                continue
                
            for stream, message_list in events:
                for message_id, message_data in message_list:
                    payload = json.loads(message_data["payload"])
                    await process_event(message_id, payload, redis_client)
                    
    except asyncio.CancelledError:
        logger.info("Worker gracefully shutting down...")
    finally:
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())