from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Backward-compatible alias for older AI modules that still import SessionLocal.
SessionLocal = AsyncSessionLocal

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session