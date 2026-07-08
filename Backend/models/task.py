# models/task.py
from datetime import datetime, date
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        index=True
    )
    
    # Links task to a specific developer in the users table
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False
    )
    
    title: Mapped[str] = mapped_column(
        String(300), 
        nullable=False
    )
    
    description: Mapped[str] = mapped_column(
        Text, 
        nullable=True
    )
    
    # Status states: todo, in_progress, done, blocked
    status: Mapped[str] = mapped_column(
        String(50), 
        default="todo", 
        nullable=False
    )
    
    due_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False
    )
    
    # Priority tiers: 1=high, 2=med, 3=low
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=2, 
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )

    # Relationship back-populates to user profile for analytics aggregation
    user = relationship("User", back_populates="tasks")