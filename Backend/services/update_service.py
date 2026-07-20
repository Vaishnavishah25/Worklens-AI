# services/update_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.daily_update import UpdateCreate
from repositories.daily_update import UpdateRepository
from models.blocker import Blocker  
from services.risk_engine import RiskEngine

class UpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UpdateRepository(db)

    async def process_and_save(self, payload: UpdateCreate, user_id: int = 1):
        # # Calculate risk penalties
        # blocker_penalty = 0.40 if payload.blockers and payload.blockers.strip() else 0.0
        # confidence_penalty = (10 - payload.confidence) * 0.06
        # score = min(1.0, blocker_penalty + confidence_penalty)
        # label = "HIGH" if score > 0.65 else "MEDIUM" if score > 0.35 else "LOW"

        # Explicit keywords assignment
        db_update = await self.repo.create_update(
            user_id=user_id,                           
            work_done=payload.work_done,                 
            next_steps=payload.next_steps,
            confidence_score=int(payload.confidence)       
        )

        # Handle Blocker logic dynamically
        if payload.blockers and payload.blockers.strip() and payload.severity != "None":
            sev_mapping = {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}
            mapped_severity = sev_mapping.get(payload.severity, "MEDIUM")

            db_blocker = Blocker(
                update_id=db_update.id,
                user_id=user_id,  
                title="Standup Form Friction Entry",
                description=payload.blockers,
                status="open",
                severity=mapped_severity  
            )
            self.db.add(db_blocker)

        await self.db.commit()
        await self.db.refresh(db_update)
        risk = await RiskEngine.get_employee_risk(self.db, user_id)
        return db_update, risk["label"]