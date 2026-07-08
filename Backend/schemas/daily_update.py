# schemas/daily_update.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UpdateCreate(BaseModel):
    employee_name: str  # Kept simple for rapid form submission mapping
    work_done: str
    blockers: Optional[str] = None
    severity: Optional[str] = None
    next_steps: str
    confidence: int

class UpdateResponse(BaseModel):
    id: int
    confidence_score: int
    work_done: str
    risk_assigned: str
    severity: Optional[str] = None
    next_steps: str

    class Config:
        from_attributes = True