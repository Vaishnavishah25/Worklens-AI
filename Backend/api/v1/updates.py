# api/v1/updates.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db # Utilizing Member 1's active async session engine
from schemas.daily_update import UpdateCreate, UpdateResponse
from services.update_service import UpdateService
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/updates", tags=["Updates"])

@router.post("/updates", status_code=status.HTTP_201_CREATED)
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
