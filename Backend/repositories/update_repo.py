# app/database/repositories/update_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.daily_update import DailyUpdate
from models.blocker import Blocker

class UpdateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, work_done: str, confidence_score: int, blocker_text: str = None) -> DailyUpdate:
        # 1. Create and save the base daily update record with all required fields
        db_update = DailyUpdate(
            user_id=1,           # Hardcoded fallback ID
            work_done=work_done,
            planned_work="Will be updated in next standup",  # Required field fallback
            confidence_score=float(confidence_score)         # Cast to float to match Model type
        )
        self.db.add(db_update)
        await self.db.flush()  # Flush pushes the record to get an ID without committing yet

        # 2. If blocker text was submitted, save it directly to the blockers table linked to this update ID
        if blocker_text and blocker_text.strip():
            db_blocker = Blocker(
                update_id=db_update.id,  # Link them together
                user_id=1,               # Hardcoded fallback matching blocker schema requirement
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

    async def get_latest_updates(self, limit: int = 10):
        result = await self.db.execute(
            select(DailyUpdate).order_by(DailyUpdate.id.desc()).limit(limit)
        )
        return result.scalars().all()