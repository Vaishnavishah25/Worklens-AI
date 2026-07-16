"""
schemas/ai.py  — Member 3
Pydantic models for all AI-related API request and response bodies.
FastAPI uses these for validation, serialisation, and Swagger docs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat / Query
# ---------------------------------------------------------------------------

class AIQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Manager's natural language question about the team.",
        examples=["Why is Priya delayed on the auth module?"],
    )
    team_id: UUID = Field(
        ...,
        description="The team whose data should be searched (scoped by JWT normally).",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Who is blocked and what should I do?",
                "team_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }


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
    latency_ms: Optional[int] = Field(
        None, description="End-to-end latency in milliseconds."
    )


# ---------------------------------------------------------------------------
# SSE chunk (streamed, not a full response body)
# ---------------------------------------------------------------------------

class SSEChunk(BaseModel):
    type: str          # "chunk" | "done" | "error"
    text: Optional[str] = None
    sources: Optional[list[SourceCitation]] = None


# ---------------------------------------------------------------------------
# Weekly summary
# ---------------------------------------------------------------------------

class WeeklySummaryRequest(BaseModel):
    team_id: UUID
    week_start_date: str = Field(
        ...,
        description="ISO date string YYYY-MM-DD for Monday of the week.",
        examples=["2024-01-08"],
    )


class WeeklySummaryResponse(BaseModel):
    team_id: UUID
    week_start_date: str
    summary: Optional[str] = Field(
        None, description="AI-generated summary text, or null if not yet generated."
    )
    no_data: bool = Field(
        False, description="True when no updates were submitted that week."
    )
    generated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class RecommendationItem(BaseModel):
    priority: int = Field(..., ge=1, le=5)
    action: str
    rationale: str
    employee: str
    urgency: str = Field(..., pattern="^(today|this_week|next_week)$")


class RecommendationsResponse(BaseModel):
    team_id: UUID
    recommendations: list[RecommendationItem]
    generated_at: datetime


# ---------------------------------------------------------------------------
# AI Guidance (employee-level)
# ---------------------------------------------------------------------------

class AIGuidanceRequest(BaseModel):
    # worklens.db uses plain integer user IDs, not UUIDs — was `UUID` before.
    employee_id: int
    team_id: Optional[str] = None


class AIGuidanceResponse(BaseModel):
    # worklens.db uses plain integer user IDs, not UUIDs — was `UUID` before.
    employee_id: int
    guidance: str = Field(
        ..., description="AI-generated guidance text for the manager about this employee."
    )
    risk_label: str
    risk_score: float
    generated_at: datetime