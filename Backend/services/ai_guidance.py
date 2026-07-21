"""
services/ai_guidance.py  — Member 3
Generates per-employee AI guidance text for managers.
Called from the dashboard when a manager clicks "Ask AI" next to an employee row,
or used to populate the guidance section of the employee detail panel.
"""

from __future__ import annotations

import logging
from datetime import datetime

from ai.embedder import embed_text
from ai.prompts import build_context_string
from ai.llm import complete
from vectorstore.faiss_store import faiss_store

from database.session import SessionLocal
from models.daily_update import DailyUpdate
from models.blocker import Blocker







logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt for employee-level guidance
# ---------------------------------------------------------------------------

_GUIDANCE_SYSTEM_PROMPT = """You are WorkLens AI.
Generate a concise manager guidance note (max 120 words) about a specific employee.

Rules:
1. Cite specific dates when referencing updates or blockers.
2. State the risk level clearly in the first sentence.
3. Give exactly 2-3 concrete actions the manager should take.
4. Do not speculate — only use data provided in the context.
5. Tone: professional, supportive, direct."""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

async def generate_employee_guidance(
    employee_id: str,
    team_id: str,
    risk_data: dict,
) -> str:
    """

    Generate a short AI guidance paragraph about one employee.

    Args:
        employee_id: UUID string
        team_id:     UUID string
        risk_data:   Dict with keys: full_name, score, label, factors,
                     open_blockers, overdue_tasks, avg_confidence_7d

    Returns:
        Guidance string (max ~120 words).
    """
    full_name = risk_data.get("full_name", "this employee")

    # Retrieve recent context about this specific employee
    query = f"{full_name} update blocker confidence risk"
# Prefer live DB grounding; if not available, fall back to FAISS.
    # 1) DB: recent daily updates + open blockers for this employee
    with SessionLocal() as session:
        updates = (
            session.query(DailyUpdate)
            .filter(DailyUpdate.employee_id == int(employee_id))
            .order_by(DailyUpdate.created_at.desc())
            .limit(6)
            .all()
        )
        open_blockers = (
            session.query(Blocker)
            .filter(Blocker.user_id == int(employee_id), Blocker.status == "open")
            .order_by(Blocker.created_at.desc())
            .limit(4)
            .all()
        )

    # SQLite schema here uses integer user_id, but our API passes UUID strings.
    # If parsing fails, skip DB grounding.
    context_parts: list[str] = []
    if updates:
        for u in updates:
            context_parts.append(
                f"[{u.created_at.date().isoformat()}] {u.work_done}"
                f" Next: {u.planned_work} (confidence {u.confidence_score}/10)"
            )
    if open_blockers:
        for b in open_blockers:
            context_parts.append(
                f"[Blocker {b.created_at.date().isoformat()}] {b.description} (severity {b.severity})"
            )

    context_text = "\n".join(context_parts).strip()
    if not context_text:
        # 2) FAISS fallback
        query_vec = await embed_text(query)
        raw_results = faiss_store.search(query_vec, k=15)

        employee_chunks = [
            r for r in raw_results
            if r.get("employee_id") == str(employee_id)
        ][:6]
        context_text = build_context_string(employee_chunks) if employee_chunks else "No recent updates found."


    # Build risk summary

    factors = risk_data.get("factors", {})

    risk_summary = (
        f"{full_name} — Risk: {risk_data.get('label', 'UNKNOWN')} "
        f"({risk_data.get('score', 0):.2f}). "
        f"Days since update: {risk_data.get('days_since_update', 'N/A')}. "
        f"Open blockers: {risk_data.get('open_blockers', 0)}. "
        f"Overdue tasks: {risk_data.get('overdue_tasks', 0)}. "
        f"Avg confidence (7d): {risk_data.get('avg_confidence_7d', 'N/A')}."
    )

    messages = [
        {"role": "system", "content": _GUIDANCE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Employee Risk Summary:\n{risk_summary}\n\n"
                f"Recent Updates from FAISS:\n{context_text}\n\n"
                "Generate manager guidance."
            ),
        },
    ]

    try:
        guidance = await complete(messages, max_tokens=200)
        return guidance.strip()
    except Exception as exc:
        logger.error("Guidance generation failed for %s: %s", employee_id, exc)
        return (
            f"{full_name} is currently rated {risk_data.get('label', 'UNKNOWN')}. "
            "Please review their recent updates manually."
        )


# ---------------------------------------------------------------------------
# Bulk guidance for the manager dashboard "team overview" view
# ---------------------------------------------------------------------------

async def generate_team_guidance(
    team_id: str,
    risk_rows: list[dict],
) -> list[dict]:
    """
    Generate guidance for every HIGH and MEDIUM risk employee on a team.
    Returns a list of {employee_id, full_name, guidance} dicts.

    Called once on dashboard load for the AI-enhanced team table.
    Only generates for HIGH / MEDIUM employees to control LLM costs.
    """
    results: list[dict] = []
    for row in risk_rows:
        if row.get("label") not in ("HIGH", "MEDIUM"):
            continue
        guidance = await generate_employee_guidance(
            employee_id=str(row["employee_id"]),
            team_id=team_id,
            risk_data=row,
        )
        results.append(
            {
                "employee_id": str(row["employee_id"]),
                "full_name": row.get("full_name", ""),
                "guidance": guidance,
                "risk_label": row.get("label"),
                "generated_at": datetime.utcnow().isoformat(),
            }
        )
    return results