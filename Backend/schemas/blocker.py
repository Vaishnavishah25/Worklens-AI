from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BlockerCreate(BaseModel):
    title: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    task_id: Optional[int] = None

class BlockerResponse(BaseModel):
    id: int
    update_id: Optional[int]
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True