# backend/schemas/feedback.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class FeedbackCreate(BaseModel):
    """
    Validates the incoming payload data when a leader authors 
    a fresh performance guidance entry.
    """
    mentee_id: int = Field(..., description="The database primary key integer of the recipient employee")
    type: Literal["praise", "guidance", "concern"] = Field(..., description="The behavioral classification tier of the note")
    visibility: Literal["employee_only", "manager_only", "public"] = Field(
        "employee_only", 
        description="The access visibility restriction scope boundary"
    )
    message: str = Field(
        ..., 
        min_length=10, 
        max_length=5000, 
        description="The core text text-body detailing the operational feedback feedback narrative"
    )

class FeedbackResponse(BaseModel):
    """
    Standardizes the serialization structure of out-bound feedback elements 
    streaming out of our PostgreSQL transactional tables.
    """
    id: int
    mentor_id: int
    mentee_id: int
    type: str
    visibility: str
    message: str
    created_at: datetime

    class Config:
        # Vital for SQLAlchemy 2.0: Instructs Pydantic to lazily evaluate 
        # and extract parameters directly from database ORM attributes.
        from_attributes = True