# Data access layer for managing daily updates in the database using SQLAlchemy's asynchronous session.
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.daily_update import DailyUpdate

class UpdateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, work_done: str, next_steps: str, confidence_score: int) -> DailyUpdate:
        db_update = DailyUpdate(
            employee_id=user_id,          
            work_done=work_done,
            next_steps=next_steps,
            confidence_score=confidence_score
        )
        self.db.add(db_update)
        await self.db.flush()  
        return db_update

    async def get_latest_updates(self, limit: int = 10):
        result = await self.db.execute(
            select(DailyUpdate).order_by(DailyUpdate.id.desc()).limit(limit)
        )
        return result.scalars().all()