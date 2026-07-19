# api/v1/employees.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.future import select
from database.session import get_db
from models.daily_update import DailyUpdate
from models.user import User
from schemas.user import UserResponse
from api.deps import get_current_user, role_required
from repositories.feedback_repo import FeedbackRepository
from repositories.task_repo import TaskRepository
from services.risk_engine import RiskEngine

router = APIRouter(prefix="/employees", tags=["Employee Profiles"])

# FIXES ISSUE 4: Explicit query parameter binding for mentor filtering
@router.get("", response_model=List[UserResponse])
async def list_employees(
    mentor_id: Optional[int] = Query(None),
    risk_label: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    query = select(User).where(User.role == "employee")
    
    # If a mentor is querying, filter strictly by their manager/mentor ID assignment
    if mentor_id is not None:
        query = query.where(User.manager_id == mentor_id)
    elif current_user.role == "mentor":
        query = query.where(User.manager_id == current_user.id)

    result = await db.execute(query)
    employees = result.scalars().all()
    return employees

@router.get("/{id}", response_model=UserResponse)
async def get_employee_profile(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor", "employee"]))
):
    # Enforce basic tenant boundaries: employees can only fetch their own profiles
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to requested profile")

    result = await db.execute(select(User).where(User.id == id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.get("/{id}/tasks")
async def get_employee_tasks(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to requested tasks")

    repo = TaskRepository(db)
    tasks = await repo.get_by_user(id)
    return [
        {
            "id": task.id,
            "task": task.title,
            "title": task.title,
            "description": task.description,
            "due": task.due_date.isoformat(),
            "due_date": task.due_date.isoformat(),
            "status": task.status,
            "risk": "High" if task.priority == 1 else "Medium" if task.priority == 2 else "Low",
            "priority": task.priority,
        }
        for task in tasks
    ]


@router.get("/{id}/feedback")
async def get_employee_feedback(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to requested feedback")

    repo = FeedbackRepository(db)
    feedback = await repo.get_feedback_for_employee(id)
    return [
        {
            "id": item.id,
            "from": str(item.mentor_id),
            "mentor_id": item.mentor_id,
            "message": item.message,
            "type": item.type,
            "date": item.created_at.strftime("%Y-%m-%d") if item.created_at else "",
            "created_at": item.created_at,
        }
        for item in feedback
    ]


@router.get("/{id}/updates")
async def get_employee_updates(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to requested updates")

    result = await db.execute(
        select(DailyUpdate)
        .where(DailyUpdate.employee_id == id)
        .order_by(DailyUpdate.created_at.desc())
    )
    updates = result.scalars().all()
    return [
        {
            "id": update.id,
            "work_done": update.work_done,
            "next_steps": update.next_steps,
            "confidence": update.confidence_score,
            "confidence_score": update.confidence_score,
            "created_at": update.created_at.isoformat() if update.created_at else "",
        }
        for update in updates
    ]


@router.get("/{id}/risk")
async def get_employee_risk(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to requested risk")

    risk = await RiskEngine.get_employee_risk(db, id)
    factors = []
    if risk["label"] != "LOW":
        factors.append("Recent confidence, blockers, or overdue work need attention.")
    return {**risk, "factors": factors}
