from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings

# asyncpg driver is used for high-performance async operations
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"), 
    echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db_session():
    """Dependency injection for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session