from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

try:
    from app.database.base import Base
except ModuleNotFoundError:
    from database.base import Base


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    team_id: Mapped[str] = mapped_column(
        String(64)
    )

    week_start_date: Mapped[str] = mapped_column(
        String(10)   # "YYYY-MM-DD"
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    no_data: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )