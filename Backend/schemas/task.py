from pydantic import BaseModel
from typing import Optional
from datetime import date

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: int
    due_date: date

class TaskUpdateStatus(BaseModel):
    status: str  # todo, in_progress, done, blocked

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: int
    due_date: date

    class Config:
        from_attributes = True