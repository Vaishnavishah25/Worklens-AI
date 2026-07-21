# app/repositories/task_repo.py
from typing import Optional, List
from datetime import datetime, timezone, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.task import Task
from sqlalchemy import func

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(self, user_id: int) -> List[Task]:
        result = await self.db.execute(
            select(Task).where(Task.employee_id == user_id).order_by(Task.due_date.asc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, title: str, description: str, priority: int, due_date: date) -> Task:
        db_task = Task(
            employee_id=user_id,
            title=title,
            description=description,
            status="todo",
            priority=priority,
            due_date=due_date
        )
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return db_task

    async def update_status(self, task_id: int, status: str) -> Optional[Task]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        db_task = result.scalar_one_or_none()
        if db_task:
            db_task.status = status
            await self.db.commit()
            await self.db.refresh(db_task)
        return db_task
    
    async def get_task_metrics(self, employee_id: int) -> tuple:
        """CONNECTS TO RISK ENGINE
        Returns (total_active_incomplete_tasks, overdue_incomplete_tasks) for a given employee_id
        """
        current_today = datetime.now(timezone.utc).date()

        total_active_query = select(func.count(Task.id)).where(
            Task.employee_id == employee_id,
            func.lower(Task.status) != "done"
        )

        overdue_query = select(func.count(Task.id)).where(
            Task.employee_id == employee_id,
            func.lower(Task.status) != "done",
            Task.due_date < current_today
        )

        total_res = await self.db.execute(total_active_query)
        overdue_res = await self.db.execute(overdue_query)

        return total_res.scalar() or 0, overdue_res.scalar() or 0