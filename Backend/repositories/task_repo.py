# app/repositories/task_repo.py
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.task import Task

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(self, user_id: int):
        result = await self.db.execute(
            select(Task).where(Task.employee_id == user_id).order_by(Task.due_date.asc())
        )
        return result.scalars().all()

    async def create(self, user_id: int, title: str, description: str, priority: int, due_date) -> Task:
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