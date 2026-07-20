# Data access layer for managing daily updates in the database using SQLAlchemy's asynchronous session.
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.daily_update import DailyUpdate
from typing import List, Optional

class UpdateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_update(self, user_id: int, work_done: str, next_steps: str, confidence_score: int) -> DailyUpdate:
        db_update = DailyUpdate(
            employee_id=user_id,          
            work_done=work_done,
            next_steps=next_steps,
            confidence_score=confidence_score
        )
        self.db.add(db_update)
        await self.db.flush()  
        return db_update

    async def get_latest_updates(self, employee_id: int) -> Optional[DailyUpdate]:
        """Queries the database for the most recent daily updates of a specific employee, limited to a specified number of entries."""
        query = select(DailyUpdate).where(DailyUpdate.employee_id == employee_id).order_by(DailyUpdate.created_at.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_updates(self, employee_id: int) -> List[DailyUpdate]:
        """Queries the database for all daily updates of a specific employee, ordered by created_at descending."""
        query = select(DailyUpdate).where(DailyUpdate.employee_id == employee_id).order_by(DailyUpdate.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
