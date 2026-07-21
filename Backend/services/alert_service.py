# backend/services/alert.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.alert import Alert
from typing import List, Optional

class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_alerts_for_leader(self, team_id: int) -> List[Alert]:
        """
        Retrieves all unacknowledged notification records bound to a supervisor's team scope.
        """
        query = (
            select(Alert)
            .where(Alert.team_id == team_id, Alert.is_acknowledged == False)
            .order_by(Alert.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def acknowledge_alert(self, alert_id: int) -> Optional[Alert]:
        """
        Flags an alert as resolved so it clears off the supervisor's dynamic tray panel.
        """
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.is_acknowledged = True
            await self.db.commit()
            await self.db.refresh(alert)
        return alert