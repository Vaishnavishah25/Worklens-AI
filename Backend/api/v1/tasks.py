# backend/api/v1/tasks.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task
from database.session import get_db
from api.deps import get_current_user, role_required
from models.user import User
from repositories.task_repo import TaskRepository
from schemas.task import TaskCreate, TaskUpdateStatus, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Task Lifecycle Management"])

@router.get("", response_model=List[TaskResponse])
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all incomplete and completed task rows bound to the caller's token context.
    """
    repo = TaskRepository(db)
    return await repo.get_by_user(user_id=current_user.id)

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def assign_task(
    payload: TaskCreate,
    employee_id: int = Query(..., description="The employee row index receiving this assignment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Delegates an operational project task assignment. 
    Clearance Level: Restricted to Managers and Mentors only.
    """
    repo = TaskRepository(db)
    return await repo.create(
        user_id=employee_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date
    )

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(
    task_id: int,
    payload: TaskUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allows developers to advance task states (e.g., to 'done' or 'blocked').
    Guards access boundaries so users cannot modify other teams' assets.
    """
    repo = TaskRepository(db)
    
    # Fetch the target task to verify ownership
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target task not found.")
        
    # Security Boundary Enforcement: regular employees can only update their own tasks
    if task.employee_id != current_user.id and current_user.role not in ["manager", "mentor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: Cannot modify tasks assigned to other developers."
        )
        
    updated = await repo.update_status(task_id, payload.status)
    return updated