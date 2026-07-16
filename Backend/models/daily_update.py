# models/daily_update.py
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from models.blocker import Blocker


class DailyUpdate(Base):
    __tablename__ = "daily_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    work_done: Mapped[str] = mapped_column(Text, nullable=False)
    next_steps: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda:datetime.now(timezone.utc).replace(tzinfo=None))

    user = relationship("User", back_populates="updates")
    blockers: Mapped[List["Blocker"]] = relationship("Blocker", back_populates="update", cascade="all, delete-orphan")