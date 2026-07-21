from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.risk_score import RiskScore
from models.user import User


class RiskRepository:

    async def create(
        self,
        db: AsyncSession,
        employee_id: int,
        score: float,
        label: str,
        team_id: int | None = None
    ) -> RiskScore:

        # If team_id not provided, query the user's team_id
        if team_id is None:
            result = await db.execute(
                select(User.team_id).where(User.id == employee_id)
            )
            user_row = result.scalar_one_or_none()
            team_id = user_row if user_row is not None else 1

        risk = RiskScore(
            employee_id=employee_id,
            score=score,
            label=label,
            team_id=team_id
        )

        db.add(risk)
        await db.commit()
        await db.refresh(risk)

        return risk

    async def get_latest_by_employee(
        self,
        db: AsyncSession,
        employee_id: int
    ) -> RiskScore | None:

        result = await db.execute(
            select(RiskScore)
            .where(RiskScore.employee_id == employee_id)
            .order_by(RiskScore.created_at.desc())
        )

        return result.scalars().first()

    async def delete_old_scores(self,db: AsyncSession,employee_id: int):
        result = await db.execute(
            select(RiskScore)
            .where(RiskScore.employee_id == employee_id)
            .order_by(RiskScore.created_at.desc())
            .offset(1)
        )
        old_scores = result.scalars().all()
        for score in old_scores:
            await db.delete(score)
        await db.commit()