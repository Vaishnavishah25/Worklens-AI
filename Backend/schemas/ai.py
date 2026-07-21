# schemas/ai.py

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field


class AIQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Manager's natural language question about the team.",
    )
    team_id: Union[int, str] = Field(
        ...,
        description="The team ID whose data should be searched.",
    )


class SourceCitation(BaseModel):
    employee: str
    date: str
    doc_type: str


class AIQueryResponse(BaseModel):
    answer: str = Field(..., description="Full AI-generated answer.")
    sources: list[SourceCitation] = Field(
        default_factory=list,
        description="Documents retrieved from FAISS that informed the answer.",
    )
    latency_ms: Optional[int] = None


class SSEChunk(BaseModel):
    type: str  # "chunk" | "done" | "error"
    text: Optional[str] = None
    sources: Optional[list[SourceCitation]] = None


class WeeklySummaryRequest(BaseModel):
    team_id: Union[int, str]
    week_start_date: str = Field(
        ...,
        description="ISO date string YYYY-MM-DD for Monday of the week.",
    )


class WeeklySummaryResponse(BaseModel):
    team_id: Union[int, str]
    week_start_date: str
    summary: Optional[str] = None
    no_data: bool = False
    generated_at: Optional[datetime] = None


class RecommendationItem(BaseModel):
    priority: int = Field(..., ge=1, le=5)
    action: str
    rationale: str
    employee: str
    urgency: str = Field(..., pattern="^(today|this_week|next_week)$")


class RecommendationsResponse(BaseModel):
    team_id: Union[int, str]
    recommendations: list[RecommendationItem]
    generated_at: datetime


class AIGuidanceRequest(BaseModel):
    employee_id: int
    team_id: Optional[Union[int, str]] = None


class AIGuidanceResponse(BaseModel):
    employee_id: int
    guidance: str
    risk_label: str
    risk_score: float
    generated_at: datetime