# api/v1/updates.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db # Utilizing Member 1's active async session engine
from schemas.daily_update import UpdateCreate, UpdateResponse
from services.update_service import UpdateService

router = APIRouter(prefix="/updates", tags=["Updates"])

@router.post("/updates", status_code=201)
async def submit_standup(payload: UpdateCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = UpdateService(db)
        db_update, risk_label = await service.process_and_save(payload, user_id=1)  # Hardcoded user_id for demonstration; replace with actual auth logic
        return {
            "id": db_update.id,
            "status": "success",
            "risk_assigned": risk_label
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))