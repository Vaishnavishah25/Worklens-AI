from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str
    priority: int = Field(2, ge=1, le=3)
    due_date: date

class TaskUpdateStatus(BaseModel):
    status: str  = Field(..., description="Must be one of: todo, in_progress, done, blocked")

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: int
    due_date: date

    class Config:
        from_attributes = True