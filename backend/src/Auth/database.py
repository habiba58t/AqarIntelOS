from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# Use async PostgreSQL connection
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/langgraph_db"
# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create tables function
async def create_auth_tables():
    from .auth_models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)