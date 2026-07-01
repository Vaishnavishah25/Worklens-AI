from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from database.base import Base


class Blocker(Base):
    __tablename__ = "blockers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    update_id: Mapped[int] = mapped_column(
        ForeignKey("daily_updates.id")
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    severity: Mapped[str] = mapped_column(
        String(20)
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="open"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="blockers"
    )

    update = relationship(
        "DailyUpdate",
        back_populates="blockers"
    )