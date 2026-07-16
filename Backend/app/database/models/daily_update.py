from datetime import datetime

from sqlalchemy import (
    Integer,
    Text,
    Float,
    ForeignKey,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

try:
    from app.database.base import Base
except ModuleNotFoundError:
    from database.base import Base


class DailyUpdate(Base):
    __tablename__ = "daily_updates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    work_done: Mapped[str] = mapped_column(
        Text
    )

    planned_work: Mapped[str] = mapped_column(
        Text
    )

    confidence_score: Mapped[float] = mapped_column(
        Float
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

