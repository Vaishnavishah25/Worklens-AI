"""
api/v1/ai.py  — Member 3
FastAPI router for all AI endpoints.

Routes:
  POST /api/v1/ai/query        — SSE streaming RAG chat
  GET  /api/v1/ai/query/sync   — Non-streaming version (for testing)
  POST /api/v1/ai/summarize    — Force-regenerate weekly summary
  GET  /api/v1/ai/summary      — Fetch cached weekly summary
  POST /api/v1/ai/recommend    — Generate JSON action items
  GET  /api/v1/ai/guidance     — Per-employee AI guidance

Rate limits:
  Standard routes: 60 req/min per IP  (handled by slowapi in main.py)
  AI routes:       10 req/min per IP  (handled by slowapi in main.py)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

try:
    from ai.rag import stream_rag_response, generate_recommendations
    from schemas.ai import (
        AIQueryRequest,
        AIQueryResponse,
        AIGuidanceRequest,
        AIGuidanceResponse,
        WeeklySummaryRequest,
        WeeklySummaryResponse,
        RecommendationItem,
        RecommendationsResponse,
    )
    from services.ai_guidance import generate_employee_guidance
    from services.summary_service import generate_team_summary
except ModuleNotFoundError:
    from ai.rag import stream_rag_response, generate_recommendations
    from schemas.ai import (
        AIQueryRequest,
        AIQueryResponse,
        AIGuidanceRequest,
        AIGuidanceResponse,
        WeeklySummaryRequest,
        WeeklySummaryResponse,
        RecommendationItem,
        RecommendationsResponse,
    )
    from services.ai_guidance import generate_employee_guidance
    from services.summary_service import generate_team_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


# ---------------------------------------------------------------------------
# Helper — get current user from JWT
# (Member 1 provides get_current_user dependency; we import it here)
# ---------------------------------------------------------------------------

def _get_current_user():
    """
    Placeholder import for Member 1's JWT dependency.
    Replace with:
        from auth.dependencies import get_current_user
    """
    try:
        from auth.dependencies import get_current_user  # type: ignore
        return Depends(get_current_user)
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Log AI interactions (writes to ai_interactions table via Member 1 repo)
# ---------------------------------------------------------------------------

async def _log_interaction(
    user_id: str,
    team_id: str,
    query: str,
    response: str,
    sources: list[dict],
    latency_ms: int,
    model: str = "gpt-4o",
) -> None:
    """Non-blocking helper to write to ai_interactions table."""
    try:
        from repositories.ai_interaction_repo import AIInteractionRepo  # type: ignore
        repo = AIInteractionRepo()
        await repo.create(
            user_id=user_id,
            team_id=team_id,
            query=query,
            response=response,
            sources_used=sources,
            model=model,
            latency_ms=latency_ms,
        )
    except ImportError:
        # During development before Member 1's repo is ready, just log it
        logger.info(
            "ai_interaction: user=%s team=%s query='%s...' latency=%dms",
            user_id, team_id, query[:60], latency_ms,
        )
    except Exception as exc:
        logger.error("Failed to log AI interaction: %s", exc)


# ---------------------------------------------------------------------------
# Route 1 — POST /ai/query  (SSE streaming)
# ---------------------------------------------------------------------------

@router.post("/query")
async def ai_query_stream(
    request: Request,
    body: AIQueryRequest,
):
    """
    Streaming RAG chat endpoint.
    Returns Server-Sent Events (SSE) with 'chunk' and 'done' events.

    Frontend should use EventSource or fetch with ReadableStream.
    """
    # Get user identity from JWT (graceful fallback for dev)
    user_id = getattr(request.state, "user_id", "dev-user")
    team_id = str(body.team_id)

    # Fetch risk data from Member 1's repo (integration point 2)
    risk_json = await _fetch_risk_json(team_id)

    start_ms = time.monotonic()

    async def event_generator():
        full_response = ""
        sources = []

        async for event in stream_rag_response(body.question, team_id, risk_json):
            event_type = event.get("type")

            if event_type == "chunk":
                full_response += event.get("text", "")
                yield f"data: {json.dumps(event)}\n\n"

            elif event_type == "done":
                sources = event.get("sources", [])
                latency = int((time.monotonic() - start_ms) * 1000)
                done_payload = {
                    "type": "done",
                    "sources": sources,
                    "latency_ms": latency,
                }
                yield f"data: {json.dumps(done_payload)}\n\n"

                # Log interaction asynchronously — don't block SSE flush
                asyncio.create_task(
                    _log_interaction(
                        user_id=user_id,
                        team_id=team_id,
                        query=body.question,
                        response=full_response,
                        sources=sources,
                        latency_ms=latency,
                    )
                )

            elif event_type == "error":
                yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",      # disables nginx buffering
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Route 2 — GET /ai/query/sync  (non-streaming, for testing/fallback)
# ---------------------------------------------------------------------------

@router.get("/query/sync", response_model=AIQueryResponse)
async def ai_query_sync(
    request: Request,
    question: str,
    team_id: UUID,
):
    """
    Non-streaming version of the AI chat endpoint.
    Returns the full answer in one JSON response.
    Useful for environments where SSE is not available.
    """
    user_id = getattr(request.state, "user_id", "dev-user")
    risk_json = await _fetch_risk_json(str(team_id))

    start_ms = time.monotonic()
    full_response = ""
    sources = []

    async for event in stream_rag_response(question, str(team_id), risk_json):
        if event["type"] == "chunk":
            full_response += event.get("text", "")
        elif event["type"] == "done":
            sources = event.get("sources", [])

    latency = int((time.monotonic() - start_ms) * 1000)

    asyncio.create_task(
        _log_interaction(
            user_id=user_id,
            team_id=str(team_id),
            query=question,
            response=full_response,
            sources=sources,
            latency_ms=latency,
        )
    )

    return AIQueryResponse(
        answer=full_response,
        sources=sources,
        latency_ms=latency,
    )


# ---------------------------------------------------------------------------
# Route 3 — POST /ai/summarize  (force regen, rate-limited to 2/day)
# ---------------------------------------------------------------------------

@router.post("/summarize", response_model=WeeklySummaryResponse)
async def force_weekly_summary(
    request: Request,
    body: WeeklySummaryRequest,
):
    """
    Force-regenerate the weekly summary for a team.
    Rate-limited to 2 requests per day per manager (enforced by slowapi).
    """
    team_id = str(body.team_id)
    week_start = body.week_start_date

    # Fetch structured week data from Member 1's repo
    week_data = await _fetch_week_data(team_id, week_start)
    team_info = await _fetch_team_info(team_id)

    # Lazy import Member 1's summary repo
    summary_repo = _get_summary_repo()

    summary_text = await generate_team_summary(
        team_id=team_id,
        team_name=team_info.get("name", "Your Team"),
        week_start_date=week_start,
        employee_summaries=week_data.get("employee_summaries", []),
        risk_rows=week_data.get("risk_rows", []),
        blocker_stats=week_data.get("blocker_stats", {"opened": 0, "resolved": 0, "still_open": 0}),
        summary_repo=summary_repo,
    )

    return WeeklySummaryResponse(
        team_id=body.team_id,
        week_start_date=week_start,
        summary=summary_text,
        no_data=(summary_text is None),
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Route 4 — GET /ai/summary  (fetch cached summary)
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    team_id: UUID,
    week_start_date: str,
):
    """
    Return the cached weekly summary for a team and week.
    Returns 404 if the summary has not been generated yet.
    """
    summary_repo = _get_summary_repo()
    try:
        row = await summary_repo.get_summary(
            team_id=str(team_id),
            week_start_date=week_start_date,
        )
    except Exception:
        row = None

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly summary not yet generated for this team and week.",
        )

    return WeeklySummaryResponse(
        team_id=team_id,
        week_start_date=week_start_date,
        summary=row.get("summary"),
        no_data=row.get("no_data", False),
        generated_at=row.get("generated_at"),
    )


# ---------------------------------------------------------------------------
# Route 5 — POST /ai/recommend  (structured JSON action items)
# ---------------------------------------------------------------------------

@router.post("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(
    team_id: UUID,
):
    """
    Generate 3-5 prioritised manager action items for a team.
    Returns a structured JSON list.
    """
    risk_json = await _fetch_risk_json(str(team_id))
    raw_recs = await generate_recommendations(str(team_id), risk_json)

    items = [
        RecommendationItem(**r)
        for r in raw_recs
        if all(k in r for k in ("priority", "action", "rationale", "employee", "urgency"))
    ]

    return RecommendationsResponse(
        team_id=team_id,
        recommendations=items,
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Route 6 — GET /ai/guidance  (per-employee guidance)
# ---------------------------------------------------------------------------

@router.get("/guidance", response_model=AIGuidanceResponse)
async def get_employee_guidance(
    employee_id: int,
    team_id: str | None = None,
):
    """
    Generate a short AI guidance note about one employee.
    Called when a manager clicks "Ask AI" next to an employee row.
    """
    risk_data = await _fetch_employee_risk(str(employee_id))

    guidance_text = await generate_employee_guidance(
        employee_id=str(employee_id),
        team_id=str(team_id),
        risk_data=risk_data,
    )

    return AIGuidanceResponse(
        employee_id=employee_id,
        guidance=guidance_text,
        risk_label=risk_data.get("label", "UNKNOWN"),
        risk_score=risk_data.get("score", 0.0),
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Integration helpers — fetch data from Member 1's repositories
# These functions wrap Member 1's repos with graceful fallbacks for dev mode
# ---------------------------------------------------------------------------

async def _fetch_risk_json(team_id: str) -> list[dict]:
    """
    Live risk data computed directly from worklens.db.
    NOTE: there is no `teams` table yet, so team_id is currently unused —
    this returns every Employee row. Narrow it once a real Team model exists.
    """
    try:
        from database.session import SessionLocal
        from models.user import User
        from models.daily_update import DailyUpdate
        from models.blocker import Blocker
        from services.risk_engine import RiskEngine
    except ModuleNotFoundError:
        from database.session import SessionLocal
        from models.user import User
        from models.daily_update import DailyUpdate
        from models.blocker import Blocker
        from services.risk_engine import RiskEngine

    rows: list[dict] = []
    try:
        with SessionLocal() as session:
            employees = session.query(User).filter(User.role == "Employee").all()
            for u in employees:
                last = (
                    session.query(DailyUpdate)
                    .filter(DailyUpdate.user_id == u.id)
                    .order_by(DailyUpdate.created_at.desc())
                    .first()
                )
                days_since = (datetime.utcnow() - last.created_at).days if last else 999

                open_blockers = (
                    session.query(Blocker)
                    .filter(Blocker.user_id == u.id, Blocker.status == "open")
                    .count()
                )

                recent = (
                    session.query(DailyUpdate.confidence_score)
                    .filter(DailyUpdate.user_id == u.id)
                    .order_by(DailyUpdate.created_at.desc())
                    .limit(7)
                    .all()
                )
                avg_conf = sum(r[0] for r in recent) / len(recent) if recent else 10

                risk = RiskEngine.calculate(
                    confidence_score=avg_conf,
                    open_blockers=open_blockers,
                    days_no_update=days_since,
                )
                rows.append({
                    "employee_id": u.id,
                    "full_name": u.name,
                    "score": risk["score"],
                    "label": risk["label"],
                    "days_since_update": days_since,
                    "open_blockers": open_blockers,
                    "avg_confidence_7d": round(avg_conf, 1),
                    "overdue_tasks": 0,  # no tasks table yet
                })
    except Exception as exc:
        logger.error("Failed to compute risk JSON for team %s: %s", team_id, exc)
        return []

    return rows


async def _fetch_employee_risk(employee_id: str) -> dict:
    """Fetch risk data for a single employee (employee_id is a real int user id)."""
    try:
        emp_id_int = int(employee_id)
    except (TypeError, ValueError):
        return {"label": "UNKNOWN", "score": 0.0, "full_name": "Employee", "factors": {}}

    for row in await _fetch_risk_json(team_id=""):
        if row["employee_id"] == emp_id_int:
            return row
    return {"label": "UNKNOWN", "score": 0.0, "full_name": "Employee", "factors": {}}


async def _fetch_week_data(team_id: str, week_start: str) -> dict:
    """Build the weekly-summary payload directly from worklens.db."""
    from datetime import timedelta

    try:
        from database.session import SessionLocal
        from models.user import User
        from models.daily_update import DailyUpdate
        from models.blocker import Blocker
        from services.risk_engine import RiskEngine
    except ModuleNotFoundError:
        from database.session import SessionLocal
        from models.user import User
        from models.daily_update import DailyUpdate
        from models.blocker import Blocker
        from services.risk_engine import RiskEngine

    empty = {"employee_summaries": [], "risk_rows": [], "blocker_stats": {"opened": 0, "resolved": 0, "still_open": 0}}

    try:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Bad week_start_date %r", week_start)
        return empty
    end = start + timedelta(days=7)

    employee_summaries: list[dict] = []
    risk_rows: list[dict] = []
    opened = resolved = still_open = 0

    try:
        with SessionLocal() as session:
            employees = session.query(User).filter(User.role == "Employee").all()
            for u in employees:
                updates = (
                    session.query(DailyUpdate)
                    .filter(
                        DailyUpdate.user_id == u.id,
                        DailyUpdate.created_at >= start,
                        DailyUpdate.created_at < end,
                    )
                    .order_by(DailyUpdate.created_at.asc())
                    .all()
                )
                if not updates:
                    continue  # nothing submitted this week — skip this employee

                week_blockers = (
                    session.query(Blocker)
                    .filter(
                        Blocker.user_id == u.id,
                        Blocker.created_at >= start,
                        Blocker.created_at < end,
                    )
                    .all()
                )
                open_count = sum(1 for b in week_blockers if b.status == "open")
                opened += len(week_blockers)
                resolved += sum(1 for b in week_blockers if b.status == "resolved")
                still_open += open_count

                employee_summaries.append({
                    "full_name": u.name,
                    "update_count": len(updates),
                    "conf_start": updates[0].confidence_score,
                    "conf_end": updates[-1].confidence_score,
                    "open_blockers": open_count,
                    "notes": None,
                })

                avg_conf = sum(x.confidence_score for x in updates) / len(updates)
                risk = RiskEngine.calculate(confidence_score=avg_conf, open_blockers=open_count)
                risk_rows.append({"full_name": u.name, "label": risk["label"], "score": risk["score"]})
    except Exception as exc:
        logger.error("Failed to fetch week data: %s", exc)
        return empty

    return {
        "employee_summaries": employee_summaries,
        "risk_rows": risk_rows,
        "blocker_stats": {"opened": opened, "resolved": resolved, "still_open": still_open},
    }


async def _fetch_team_info(team_id: str) -> dict:
    """
    No `teams` table exists yet, so this derives a display name from the
    single manager in worklens.db rather than hardcoding a fake name.
    """
    try:
        from database.session import SessionLocal
        from models.user import User
    except ModuleNotFoundError:
        from database.session import SessionLocal
        from models.user import User

    try:
        with SessionLocal() as session:
            manager = session.query(User).filter(User.role == "Manager").first()
        return {"name": f"{manager.name}'s Team" if manager else "Your Team"}
    except Exception as exc:
        logger.error("Failed to fetch team info: %s", exc)
        return {"name": "Your Team"}


def _get_summary_repo():
    try:
        from repositories.summary_repository import SummaryRepository
    except ModuleNotFoundError:
        from repositories.summary_repository import SummaryRepository
    return SummaryRepository()