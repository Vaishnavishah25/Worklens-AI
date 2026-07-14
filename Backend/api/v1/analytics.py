# backend/api/v1/analytics.py
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.session import get_db
from api.deps import get_current_user, role_required
from models.user import User
from schemas.analytics import TeamHealthTrendResponse
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Operational Analytics"])

@router.get("/team", response_model=TeamHealthTrendResponse)
async def get_team_health_trend(
    team_id: int = Query(..., description="The organization team database index"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"])) # Locked down to leadership roles
):
    """
    Exposes weekly historical health scores used to render dynamic Plotly charts 
    on the supervisor dashboard console.
    """
    service = AnalyticsService(db)
    # The service layers aggregate raw database parameters and output formatted metrics
    return await service.get_historical_trends(team_id=team_id)