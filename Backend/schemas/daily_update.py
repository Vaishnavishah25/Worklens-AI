# schemas/daily_update.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UpdateCreate(BaseModel):
    work_done: str = Field(..., min_length=10)
    next_steps: str = Field(..., min_length=10)
    confidence: int = Field(..., ge=1, le=10)
    blockers: Optional[str] = None
    severity: Optional[str] = None

class UpdateResponse(BaseModel):
    id: int
    employee_id: int
    work_done: str
    next_steps: str
    confidence_score: int
    created_at: datetime

    risk_assigned: str
    severity: Optional[str] = None

    class Config:
        from_attributes = True