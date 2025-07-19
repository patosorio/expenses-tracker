from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Create the async SQLAlchemy engine
try:
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DB_ECHO,
    )
except ImportError:
    # Fallback for environments without asyncpg (like during migrations)
    engine = None

# SYNC Engine (for Alembic migrations)
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://").replace("postgresql://", "postgresql+psycopg2://"),
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_size=10,
    max_overflow=20,
    echo=settings.DB_ECHO
)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=settings.DB_EXPIRE_ON_COMMIT
) if engine else None

# Create sync session factory (for migrations and scripts)
SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False
)

# Create a Base class for declarative models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency function to get a database session.
    Usage in FastAPI:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Async database session not available")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """
    Sync session for migrations and scripts.
    Usage:
        with get_sync_db() as db:
            # sync operations
    """
    with SyncSessionLocal() as session:
        try:
            yield session
        finally:
            session.close()

@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database, creating all tables."""
    if not engine:
        raise RuntimeError("Async database engine not available")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)