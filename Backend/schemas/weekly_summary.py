# schemas/weekly_summary.py

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field


class WeeklySummaryCreate(BaseModel):
    team_id: Union[int, str]
    week_start_date: str = Field(..., description="YYYY-MM-DD format")
    summary: Optional[str] = None
    no_data: bool = False


class WeeklySummaryResponse(BaseModel):
    id: int
    team_id: Union[int, str]
    week_start_date: str
    summary: Optional[str] = None
    no_data: bool = False
    generated_at: datetime

    class Config:
        from_attributes = True