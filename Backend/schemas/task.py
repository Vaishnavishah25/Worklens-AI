from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    priority: int = Field(2, ge=1, le=3)
    due_date: date

class TaskUpdateStatus(BaseModel):
    status: str  = Field(..., description="Must be one of: todo, in_progress, done, blocked")

class TaskResponse(BaseModel):
    id: int
    employee_id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    due_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True