from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.risk_score import RiskScore


class RiskRepository:

    async def create(
        self,
        db: AsyncSession,
        employee_id: int,
        score: float,
        label: str
    ) -> RiskScore:

        risk = RiskScore(
            employee_id=employee_id,
            score=score,
            label=label
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
        old_scores = result.scalar().all()
        for score in old_scores:
            await db.delete(score)
        await db.commit()