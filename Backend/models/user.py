# backend/models/user.py

from __future__ import annotations

from sqlalchemy import (
    Integer,
    Column,
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

    hashed_password: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[str] = mapped_column(
        String(50)
    )

    team_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("teams.id"),
        nullable=True
    )

    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    manager = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[manager_id]
    )

    team = relationship(
        "Team",
        back_populates="members",
        foreign_keys=[team_id]
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
    
    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    feedback_given = relationship(
        "Feedback",
        foreign_keys="[Feedback.mentor_id]",
        back_populates="mentor"
    )
    
    feedback_received = relationship(
        "Feedback",
        foreign_keys="[Feedback.mentee_id]",
        back_populates="mentee"
    )