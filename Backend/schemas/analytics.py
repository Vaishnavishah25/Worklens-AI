# backend/schemas/analytics.py
from pydantic import BaseModel
from typing import List, Dict

class TeamHealthTrendResponse(BaseModel):
    labels: List[str]  # e.g., ["Week 1", "Week 2", "Week 3"]
    health_scores: List[float]  # e.g., [82.5, 84.0, 85.2]

class BlockerMetrics(BaseModel):
    total_reported: int
    active_open: int
    resolution_rate: float

class PerformanceIndicators(BaseModel):
    update_streak_days: int
    avg_confidence_score: float
    task_completion_velocity: float

    class Config:
        from_attributes = True