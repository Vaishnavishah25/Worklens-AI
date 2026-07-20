from repositories.task_repo import TaskRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from models.daily_update import DailyUpdate
from models.blocker import Blocker

class RiskEngine:

    @staticmethod
    def calculate(
        confidence_score: float,
        open_blockers: int,
        days_no_update: int = 0,
        overdue_tasks: int = 0,
        total_tasks: int = 1
    ):

        d_norm = min(days_no_update / 7, 1.0)

        b_norm = min(open_blockers / 3, 1.0)

        c_norm = (5 - confidence_score) / 4

        t_norm = (
            min(overdue_tasks / total_tasks, 1.0)
            if total_tasks > 0
            else 0
        )

        score = (
            0.35 * d_norm +
            0.25 * b_norm +
            0.25 * c_norm +
            0.15 * t_norm
        )

        if score < 0.3:
            label = "LOW"
        elif score < 0.6:
            label = "MEDIUM"
        else:
            label = "HIGH"

        return {
            "score": round(score, 2),
            "label": label
        }
    
    @classmethod
    async def get_employee_risk (cls, db: AsyncSession, employee_id: int) -> dict:
        """DYNAMIC COMPILING LAYER
        Queries live operational tables to assemble metrics and feeds them into the core mathematical scoring core"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Fetch days since last update component
        update_query = (
            select(DailyUpdate)
            .where(DailyUpdate.employee_id == employee_id)
            .order_by(DailyUpdate.created_at.desc())
            .limit(1)
        )
        update_res = await db.execute(update_query)
        latest_update = update_res.scalar_one_or_none()

        days_no_update = (now - latest_update.created_at).days if latest_update else 7
        confidence = int(latest_update.confidence_score) if latest_update else 5

        # Fetch active blockers accumulations (case-insensitive status match)
        blocker_query = (
            select(func.count(Blocker.id))
            .where(Blocker.user_id == employee_id, func.lower(Blocker.status) == "open")
        )
        blocker_res = await db.execute(blocker_query)
        open_blockers = blocker_res.scalar() or 0

        # Fetch task lifecycles from TaskRepository
        task_repo = TaskRepository(db)
        all_tasks = await task_repo.get_by_user(employee_id)

        total_tasks = len([t for t in all_tasks if t.status != "done"])
        overdue_tasks = len([t for t in all_tasks if t.status != "done" and t.due_date < now.date()])

        # Execute pure mathematical calculation pass
        return cls.calculate(
            confidence_score=confidence,
            open_blockers=open_blockers,
            days_no_update=days_no_update,
            overdue_tasks=overdue_tasks,
            total_tasks=max(total_tasks, 1)
        )
