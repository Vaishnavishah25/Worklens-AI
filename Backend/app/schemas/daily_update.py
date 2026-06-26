# app/schemas/update.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UpdateCreate(BaseModel):
    employee_name: str  # Kept simple for rapid form submission mapping
    work_done: str
    blockers: Optional[str] = None
    confidence: int

class UpdateResponse(BaseModel):
    id: int
    confidence_score: int
    work_done: str
    risk_assigned: str

    class Config:
        from_attributes = True