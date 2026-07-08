# app/database/models/daily_update.py
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    DateTime,
    Float,
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    work_done: Mapped[str] = mapped_column(Text)
    next_steps: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="updates")
    blockers: Mapped[List["Blocker"]] = relationship("Blocker", back_populates="update", cascade="all, delete-orphan")