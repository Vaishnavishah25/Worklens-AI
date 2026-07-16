# backend/services/alert.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from typing import List, Optional
from datetime import datetime, timezone

# Quick fallback structural model wrapper to keep things simple for the MVP
# If you haven't run migrations for an explicit alerts table yet, you can map this out.
from database.base import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(100))  # e.g., "no_update_3d", "high_risk_drop"
    message: Mapped[str] = mapped_column(String(500))
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

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