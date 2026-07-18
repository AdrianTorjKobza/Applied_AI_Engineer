import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from src.infrastructure.database.models import UserAffinity
from src.config import settings

async def verify_data():
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    
    async with engine.connect() as conn:
        print(f"Connecting to: {settings.database_url}")
        # Simple query to fetch all users in the affinity table
        result = await conn.execute(select(UserAffinity))
        affinities = result.fetchall()
        
        print(f"\n--- Found {len(affinities)} User Profiles in Database ---")
        for user in affinities:
            print(f"User: {user.user_id} | Scores: Running: {user.score_running:.2f}, Weightlifting: {user.score_weightlifting:.2f}, Outdoor: {user.score_outdoor:.2f}")

if __name__ == "__main__":
    asyncio.run(verify_data())