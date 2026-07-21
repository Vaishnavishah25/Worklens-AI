# backend/models/alert.py
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Nullable to prevent crash if team is unassigned
    type: Mapped[str] = mapped_column(String(100))  # e.g., "no_update_3d", "high_risk_drop"
    message: Mapped[str] = mapped_column(String(500))
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )