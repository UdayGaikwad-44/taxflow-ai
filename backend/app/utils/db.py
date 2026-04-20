import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base  # ensures all models are imported/registered
from app.utils.settings import settings

DATABASE_URL = os.getenv("DATABASE_URL") or settings.database_url
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Provide an async URL like postgresql+asyncpg://user:pass@host:5432/db")

async_engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


async def create_all() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

