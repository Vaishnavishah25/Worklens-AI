# backend/models/feedback.py
from datetime import datetime, timezone
from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20)) # praise / guidance / concern
    visibility: Mapped[str] = mapped_column(String(30), default="employee_only")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Converted to a dynamic runtime lambda stripping tzinfo to avoid asyncpg mismatches
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="feedback_given")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="feedback_received")