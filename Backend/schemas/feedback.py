# backend/schemas/feedback.py

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """
    Validates payload when a mentor/leader creates a feedback entry.
    """
    mentee_id: int = Field(..., description="The user ID of the recipient employee")
    type: Literal["praise", "guidance", "concern"] = Field(
        ..., description="Behavioral classification tier of the feedback"
    )
    visibility: Literal["employee_only", "manager_only", "public"] = Field(
        "employee_only", 
        description="Access visibility restriction boundary"
    )
    message: str = Field(
        ..., 
        min_length=10, 
        max_length=5000, 
        description="Core message content detailing the feedback"
    )


class FeedbackResponse(BaseModel):
    """
    Outbound response structure for feedback items.
    """
    id: int
    mentor_id: int
    mentee_id: int
    type: str
    visibility: str
    message: str
    created_at: datetime

    # Display attributes enriched at service/router level
    mentor_name: Optional[str] = None
    mentee_name: Optional[str] = None

    class Config:
        from_attributes = True