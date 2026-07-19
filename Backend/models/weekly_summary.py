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

from database.base import Base


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    team_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    week_start_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    no_data: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )