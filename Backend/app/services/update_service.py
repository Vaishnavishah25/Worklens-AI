# app/services/update_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.update_repo import UpdateRepository
from app.schemas.daily_update import UpdateCreate

class UpdateService:
    def __init__(self, db: AsyncSession):
        self.repo = UpdateRepository(db)

    async def process_and_save(self, payload: UpdateCreate):
        # Operational Risk Calculation on the fly
        blocker_penalty = 0.40 if payload.blockers and len(payload.blockers.strip()) > 3 else 0.0
        confidence_penalty = (10 - payload.confidence) * 0.06
        score = min(1.0, blocker_penalty + confidence_penalty)
        label = "HIGH" if score > 0.65 else "MEDIUM" if score > 0.35 else "LOW"
        
        # Pass the blocker text to the repository creator method
        db_update = await self.repo.create(
            work_done=payload.work_done,
            confidence_score=payload.confidence,
            blocker_text=payload.blockers  # Added here
        )
        
        return db_update, label