# api/v1/employees.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.future import select
from database.session import get_db
from models.user import User
from schemas.user import UserResponse
from api.deps import role_required

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