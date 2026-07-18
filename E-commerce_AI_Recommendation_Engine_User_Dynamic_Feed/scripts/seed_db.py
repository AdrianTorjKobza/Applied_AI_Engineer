import asyncio
import uuid
import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Adjust path to import from src
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import settings
from src.infrastructure.database.models import Base, Product

async def seed():
    # Initialize async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    
    # Create tables if they do not exist
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Seed dummy products
    async with AsyncSessionLocal() as session:
        # Check if products already exist
        from sqlalchemy import select
        result = await session.execute(select(Product).limit(1))
        
        if result.first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding dummy products...")
        base_products = [
            ("Trailblazer Running Shoes", 0.9, 0.0, 0.3),
            ("Olympic Barbell 20kg", 0.0, 1.0, 0.0),
            ("Gore-Tex Hiking Jacket", 0.2, 0.0, 0.9),
            ("Carbon Fiber Trekking Poles", 0.3, 0.0, 0.8),
            ("Compression Sprint Tights", 0.8, 0.2, 0.1),
            ("Kettlebell Set (16-24kg)", 0.0, 0.9, 0.1),
            ("Ultra-light Hydration Pack", 0.7, 0.0, 0.8),
            ("Squat Rack with Pull-up Bar", 0.0, 1.0, 0.0),
            ("All-Terrain Trail Runners", 0.8, 0.0, 0.6),
            ("Chalk Bag & Climbing Harness", 0.1, 0.4, 0.9),
        ]

        for name, w_run, w_weight, w_out in base_products:
            prod = Product(
                id=f"prod_{str(uuid.uuid4())[:8]}",
                name=name,
                weight_running=w_run,
                weight_weightlifting=w_weight,
                weight_outdoor=w_out
            )
            session.add(prod)
            
        await session.commit()
        print("Successfully seeded database with 10 products.")

if __name__ == "__main__":
    asyncio.run(seed())