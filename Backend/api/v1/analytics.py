# backend/api/v1/analytics.py
import logging
from collections import defaultdict
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from database.session import get_db
from api.deps import get_current_user, role_required
from models.user import User
from models.blocker import Blocker
from schemas.analytics import TeamHealthTrendResponse
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Operational Analytics"])
logger = logging.getLogger(__name__)


@router.get("/team", response_model=TeamHealthTrendResponse)
async def get_team_health_trend(
    team_id: Optional[int] = Query(None, description="The organization team database index"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Exposes weekly historical health scores used to render dynamic Plotly charts 
    on the supervisor dashboard console.
    """
    try:
        # Fallback logic: if team_id not provided, use current_user's team_id or id
        effective_team_id = team_id
        if effective_team_id is None:
            # Try to get team_id from user, fallback to user's own id
            effective_team_id = getattr(current_user, 'team_id', None) or current_user.id
        
        service = AnalyticsService(db)
        result = await service.get_historical_trends(team_id=effective_team_id)
        
        # Ensure we have the required keys
        if result is None or not isinstance(result, dict):
            return {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                "health_scores": [100.0, 100.0, 100.0, 100.0, 100.0]
            }
        
        # Ensure health_scores key exists (fallback to health if needed)
        if "health_scores" not in result and "health" in result:
            result["health_scores"] = result["health"]
        if "health_scores" not in result:
            result["health_scores"] = [100.0, 100.0, 100.0, 100.0, 100.0]
        if "labels" not in result:
            result["labels"] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        
        return result
    except Exception as e:
        logger.exception(f"Error in get_team_health_trend: {e}")
        return {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "health_scores": [100.0, 100.0, 100.0, 100.0, 100.0]
        }


@router.get("/blockers")
async def get_blocker_analytics(
    weeks: int = Query(4, description="Number of weeks to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Returns weekly blocker counts as a time-series for chart rendering.
    Uses Python aggregation for cross-database compatibility.
    """
    try:
        # Calculate the start date for the query window
        start_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        # Query all blockers in the time window using standard SQL (no date_trunc)
        result = await db.execute(
            select(Blocker.created_at)
            .where(Blocker.created_at >= start_date)
        )
        rows = result.all()
        
        # Aggregate by week in Python (cross-database compatible)
        week_counts = defaultdict(int)
        
        for row in rows:
            created_at = row[0]
            if created_at:
                # Week number of the year (Monday as first day)
                week_label = f"Week {created_at.strftime('%U')}"
                week_counts[week_label] += 1
        
        # If no data, generate placeholder weeks
        if not week_counts:
            labels = [f"Week {i:02d}" for i in range(weeks)]
            counts = [0] * weeks
        else:
            # Sort by week number
            sorted_weeks = sorted(week_counts.items(), key=lambda x: int(x[0].split()[-1]))
            labels = [item[0] for item in sorted_weeks]
            counts = [item[1] for item in sorted_weeks]
        
        return {
            "labels": labels,
            "counts": counts
        }
    except Exception as e:
        logger.exception(f"Error in get_blocker_analytics: {e}")
        return {
            "labels": [f"Week {i:02d}" for i in range(weeks)],
            "counts": [0] * weeks
        }