from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BlockerCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    task_id: Optional[int] = None

class BlockerResponse(BaseModel):
    id: int
    user_id: int
    update_id: Optional[int] = None
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True