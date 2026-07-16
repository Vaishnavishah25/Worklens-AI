# backend/api/v1/feedback.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from repositories.feedback_repo import FeedbackRepository
from schemas.feedback import FeedbackCreate, FeedbackResponse
from api.deps import get_current_user, role_required
from models.user import User

router = APIRouter(prefix="/feedback", tags=["Mentor Feedback"])

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Saves professional mentor guidance commentary logs. 
    Binds the primary authorship ID directly to the verified session context token.
    """
    repo = FeedbackRepository(db)
    feedback = await repo.create(
        mentor_id=current_user.id,
        mentee_id=payload.mentee_id,
        feedback_type=payload.type,
        visibility=payload.visibility,
        message=payload.message
    )
    return feedback

@router.get("/mentor/{mentor_id}", response_model=List[FeedbackResponse])
async def get_feedback_given(
    mentor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"])) # ⛑️ FIXED: Guarded route access
):
    repo = FeedbackRepository(db)
    return await repo.get_feedback_by_mentor(mentor_id)

@router.get("/employee/{employee_id}", response_model=List[FeedbackResponse])
async def get_feedback_received(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Security Boundary Enforcement: Employees should only read feedback explicitly directed to them
    if current_user.role == "employee" and current_user.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view feedback logs targeted at other personnel."
        )
    repo = FeedbackRepository(db)
    return await repo.get_feedback_for_employee(employee_id)

@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = FeedbackRepository(db)
    feedback = await repo.get_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback log entry not found")
        
    # Enforce standard visibility scope limits
    if current_user.role == "employee" and current_user.id != feedback.mentee_id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this item.")
    return feedback

@router.delete("/{feedback_id}", response_model=FeedbackResponse)
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    repo = FeedbackRepository(db)
    
    # Optional context validation: Mentors can only delete feedback they originally authored
    existing_feedback = await repo.get_by_id(feedback_id)
    if existing_feedback and current_user.role == "mentor" and existing_feedback.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation rejected: Mentors can only remove logs they authored.")

    deleted = await repo.delete(feedback_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback entry not found")
    return deleted