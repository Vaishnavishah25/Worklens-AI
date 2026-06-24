import asyncio

from sqlalchemy import text
from app.database.session import engine


async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Database Response:", result.scalar())


asyncio.run(test())