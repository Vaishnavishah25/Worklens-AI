# app/database/repositories/update_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.daily_update import DailyUpdate
from models.blocker import Blocker
from typing import Optional, List

class UpdateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_update(
        self,
        user_id: str,
        work_done: str,
        next_steps: str,
        confidence_score: int,
        blocker_text: str = None,
    ) -> DailyUpdate:
        # 1. Create and save the base daily update record with all required fields
        db_update = DailyUpdate(
            employee_id=user_id,  # Hardcoded fallback ID
            work_done=work_done,
            next_steps=next_steps,
            confidence_score=int(confidence_score)
        )
        self.db.add(db_update)
        await self.db.flush()  # Flush pushes the record to get an ID without committing yet

        # 2. If blocker text was submitted, save it directly to the blockers table linked to this update ID
        if blocker_text and blocker_text.strip():
            db_blocker = Blocker(
                update_id=db_update.id,  # Link them together
                user_id=user_id,         # Hardcoded fallback matching blocker schema requirement
                title="System Blocker Flag",
                description=blocker_text,
                status="open",           # Default status for MVP
                severity="HIGH" if confidence_score < 4 else "MEDIUM"
            )
            self.db.add(db_blocker)

        # 3. Commit both records safely in a single transaction
        await self.db.commit()
        await self.db.refresh(db_update)
        return db_update

    async def get_latest_updates(
        self,
        employee_id: Optional[int] = None,
        limit: int = 10
    ) -> List[DailyUpdate]:
        query = select(DailyUpdate)
        if employee_id is not None:
            query = query.where(DailyUpdate.employee_id == employee_id)
        
        query = query.order_by(DailyUpdate.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_updates(self, employee_id: int) -> List[DailyUpdate]:
        query = (
            select(DailyUpdate)
            .where(DailyUpdate.employee_id == employee_id)
            .order_by(DailyUpdate.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
