# backend/tasks/risk_calc.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from models.risk_score import RiskScore
from services.risk_engine import RiskEngine
from datetime import datetime, timezone

async def run_periodic_risk_recalculation(db: AsyncSession):
    """
    Background worker that runs calculations across active accounts 
    and updates cached snapshots to keep dashboard views synchronized.
    """
    # 1. Gather all system developers subject to evaluation
    user_query = select(User).where(User.role == "employee")
    user_res = await db.execute(user_query)
    employees = user_res.scalars().all()

    for emp in employees:
        # Calculate dynamic risk score vector from active live logs
        metrics = await RiskEngine.get_employee_risk(db, employee_id=emp.id)
        
        # 2. Check if a pre-existing cached row exists
        score_query = select(RiskScore).where(RiskScore.employee_id == emp.id)
        score_res = await db.execute(score_query)
        cached_score = score_res.scalar_one_or_none()

        if cached_score:
            cached_score.score = metrics["score"]
            cached_score.label = metrics["label"]
            cached_score.team_id = emp.team_id
            cached_score.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # First time record construction using user's dynamic team_id
            new_score = RiskScore(
                employee_id=emp.id,
                score=metrics["score"],
                label=metrics["label"],
                team_id=emp.team_id
            )
            db.add(new_score)
            
    await db.commit()