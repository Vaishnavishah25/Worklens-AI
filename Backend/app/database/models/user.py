from sqlalchemy import (
    Integer,
    String,
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True
    )

    password: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[str] = mapped_column(
        String(50)
    )

    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    manager = relationship(
        "User",
        remote_side=[id]
    )

    updates = relationship(
        "DailyUpdate",
        back_populates="user"
    )
    blockers = relationship(
        "Blocker",
        back_populates="user"
    )

    risk_scores = relationship(
    "RiskScore",
    back_populates="employee"
)