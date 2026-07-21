# backend/schemas/analytics.py

from typing import List, Union
from pydantic import BaseModel, Field


class TeamHealthResponse(BaseModel):
    team_id: Union[int, str]
    health_score: float = Field(..., ge=0.0, le=100.0)


class TeamHealthTrendResponse(BaseModel):
    labels: List[str]  # e.g., ["Week 25", "Week 26", "Week 27", "Current"]
    health_scores: List[float]


class BlockerMetricsResponse(BaseModel):
    open: int
    resolved: int
    escalated: int
    total: int


class TaskMetricsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    completion_rate: float


class PerformanceIndicators(BaseModel):
    update_streak_days: int
    avg_confidence_score: float
    task_completion_velocity: float

    class Config:
        from_attributes = True