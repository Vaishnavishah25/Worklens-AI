# backend/services/update_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.daily_update import UpdateCreate
from repositories.update_repo import UpdateRepository
from repositories.risk_repository import RiskRepository
from models.blocker import Blocker
from models.user import User
from services.risk_engine import RiskEngine
from tasks.alert_scan import scan_and_generate_risk_alerts


class UpdateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UpdateRepository(db)
        self.risk_repo = RiskRepository()

    async def process_and_save(self, payload: UpdateCreate, user_id: int = 1):
        # 1. Save base daily update record
        db_update = await self.repo.create_update(
            user_id=user_id,
            work_done=payload.work_done,
            next_steps=payload.next_steps,
            confidence_score=int(payload.confidence)
        )

        # 2. Handle Blocker logic dynamically
        if payload.blockers and payload.blockers.strip() and payload.severity != "None":
            raw_sev = str(payload.severity).lower().strip()
            sev_mapping = {
                "none": "LOW", "low": "LOW", "1": "LOW",
                "medium": "MEDIUM", "2": "MEDIUM",
                "high": "HIGH", "critical": "HIGH", "3": "HIGH"
            }
            mapped_severity = sev_mapping.get(raw_sev, "MEDIUM")

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

        # 3. Resolve user's dynamic team_id
        user_res = await self.db.execute(select(User.team_id).where(User.id == user_id))
        user_team_id = user_res.scalar_one_or_none()

        # 4. Calculate risk and persist to risk_scores table
        risk = await RiskEngine.get_employee_risk(self.db, user_id)
        await self.risk_repo.create(
            db=self.db,
            employee_id=user_id,
            score=risk["score"],
            label=risk["label"],
            team_id=user_team_id
        )

        # 5. Trigger alert scanning for risk events
        await scan_and_generate_risk_alerts(self.db)

        return db_update, risk["label"]