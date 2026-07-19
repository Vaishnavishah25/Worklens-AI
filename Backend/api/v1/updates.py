# api/v1/updates.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db # Utilizing Member 1's active async session engine
from schemas.daily_update import UpdateCreate, UpdateResponse
from services.update_service import UpdateService
from api.deps import get_current_user
from models.user import User

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
    service = UpdateService(db)
    latest = await service.repo.get_latest_updates(current_user.id)
    if not latest:
        return None
    return {
        "id": latest.id,
        "work_done": latest.work_done,
        "next_steps": latest.next_steps,
        "confidence": latest.confidence_score,
        "confidence_score": latest.confidence_score,
        "created_at": latest.created_at.isoformat() if latest.created_at else "",
    }
