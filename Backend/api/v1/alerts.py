# backend/api/v1/alerts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database.session import get_db
from api.deps import get_current_user, role_required
from models.user import User
from services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["System Risk Alerts"])

# Inlined clean schema verification classes to keep delivery localized
class AlertResponse(BaseModel):
    id: int
    employee_id: int
    team_id: int
    type: str
    message: str
    is_acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[AlertResponse])
async def get_unacknowledged_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"])) # Locked to leadership
):
    """
    Returns a live, real-time list of all active, unacknowledged exceptions requiring intervention.
    """
    # Fallback to current mentor's active team scope (e.g., team_id: 2)
    # In a fully populated organization, this pulls dynamically from current_user.team_id
    team_scope = getattr(current_user, "team_id", 2) or 2
    
    service = AlertService(db)
    return await service.get_active_alerts_for_leader(team_id=team_scope)

@router.put("/{alert_id}/ack", response_model=AlertResponse)
async def acknowledge_system_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Marks a specific anomaly exception flag as acknowledged.
    """
    service = AlertService(db)
    updated_alert = await service.acknowledge_alert(alert_id=alert_id)
    
    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Target system alert log item not found."
        )
    return updated_alert