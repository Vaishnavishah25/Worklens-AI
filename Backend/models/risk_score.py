from datetime import datetime

from sqlalchemy import (
    Integer,
    Float,
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from database.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),index=True
    )

    score: Mapped[float] = mapped_column(
        Float
    )

    label: Mapped[str] = mapped_column(
        String(20)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    employee = relationship(
        "User",
        back_populates="risk_scores"
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )