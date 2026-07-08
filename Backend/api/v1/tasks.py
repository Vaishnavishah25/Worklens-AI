# app/v1/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database.session import get_db
from schemas.task import TaskCreate, TaskResponse, TaskUpdateStatus
from repositories.task_repo import TaskRepository

router = APIRouter(prefix="/tasks", tags=["Employee Tasks"])

@router.get("", response_model=List[TaskResponse])
async def get_my_tasks(db: AsyncSession = Depends(get_db)):
    repo = TaskRepository(db)
    # Baseline fallback user context for hackathon MVP stability
    return await repo.get_by_user(user_id=1)

@router.post("", response_model=TaskResponse, status_code=201)
async def create_new_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    repo = TaskRepository(db)
    return await repo.create(
        user_id=1,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date
    )

@router.put("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(task_id: int, payload: TaskUpdateStatus, db: AsyncSession = Depends(get_db)):
    repo = TaskRepository(db)
    updated = await repo.update_status(task_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Task record not found")
    return updated