# api/v1/updates.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_db # Utilizing Member 1's active async session engine
from schemas.daily_update import UpdateCreate, UpdateResponse
from services.update_service import UpdateService
from api.deps import get_current_user
from models.user import User
from models.daily_update import DailyUpdate

router = APIRouter(prefix="/updates", tags=["Updates"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_standup(payload: UpdateCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ingets team updates securely. Provides a risk label based on confidence score and other metrics."""
    try:
        service = UpdateService(db)
        db_update, risk_label = await service.process_and_save(payload, user_id=current_user.id)
        return {
            "id": db_update.id,
            "status": "success",
            "risk_assigned": risk_label
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/updates", status_code=status.HTTP_201_CREATED)
async def submit_standup_legacy(payload: UpdateCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await submit_standup(payload, db, current_user)


@router.get("/today")
async def get_today_update(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get the daily update for the current user created today (since 00:00 UTC).
    Raises HTTP 404 if no update exists for today.
    """
    # Calculate today's start (00:00 UTC)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )
    
    # Query for update created today
    result = await db.execute(
        select(DailyUpdate)
        .where(DailyUpdate.employee_id == current_user.id)
        .where(DailyUpdate.created_at >= today_start)
        .order_by(DailyUpdate.created_at.desc())
        .limit(1)
    )
    today_update = result.scalar_one_or_none()
    
    if not today_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No update found for today")
    
    return {
        "id": today_update.id,
        "work_done": today_update.work_done,
        "next_steps": today_update.next_steps,
        "confidence": today_update.confidence_score,
        "confidence_score": today_update.confidence_score,
        "created_at": today_update.created_at.isoformat() if today_update.created_at else "",
    }
