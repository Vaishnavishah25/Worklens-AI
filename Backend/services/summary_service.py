"""
services/summary_service.py  — Member 3
Generates and caches weekly team summaries using the LLM.

Called by:
  1. APScheduler every Sunday at 23:00 UTC  →  generate_all_team_summaries()
  2. POST /api/v1/ai/summarize              →  generate_team_summary() (force regen)

Reads:   daily_updates, risk_scores, blockers (via Member 1 repos)
Writes:  weekly_summaries table (via Member 1 repo hook)
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta, datetime

from ai.llm import complete
from ai.prompts import build_summary_messages

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public: single-team summary
# ---------------------------------------------------------------------------

async def generate_team_summary(
    team_id: str,
    team_name: str,
    week_start_date: date,
    employee_summaries: list[dict],
    risk_rows: list[dict],
    blocker_stats: dict,
    summary_repo,               # Member 1 repo — has upsert_summary(...)
) -> str | None:
    """
    Generate and cache a weekly summary for one team.

    Args:
        team_id:            UUID string
        team_name:          Human-readable team name
        week_start_date:    Monday of the target week
        employee_summaries: Per-employee stats built by Member 1's analytics service
            Each dict needs: full_name, update_count, conf_start, conf_end,
                             open_blockers, notes (optional)
        risk_rows:          End-of-week risk rows from risk_scores table
            Each dict needs: full_name, label, score
        blocker_stats:      {"opened": int, "resolved": int, "still_open": int}
        summary_repo:       Member 1 repository with .upsert_summary() method

    Returns:
        The generated summary text, or None on failure.
    """
    # Safety check — skip if no data
    if not employee_summaries:
        await summary_repo.upsert_summary(
            team_id=team_id,
            week_start_date=str(week_start_date),
            summary=None,
            no_data=True,
            generated_at=datetime.utcnow(),
        )
        logger.info("Skipped summary for team %s — no updates this week", team_id)
        return None

    week_label = _format_week_label(week_start_date)

    messages = build_summary_messages(
        team_name=team_name,
        week_label=week_label,
        employee_summaries=employee_summaries,
        risk_rows=risk_rows,
        blocker_stats=blocker_stats,
    )

    try:
        summary_text = await complete(messages, max_tokens=600)
        summary_text = summary_text.strip()
    except Exception as exc:
        logger.error("LLM summary generation failed for team %s: %s", team_id, exc)
        return None

    # Persist to weekly_summaries via Member 1's repo
    await summary_repo.upsert_summary(
        team_id=team_id,
        week_start_date=str(week_start_date),
        summary=summary_text,
        no_data=False,
        generated_at=datetime.utcnow(),
    )

    logger.info(
        "Weekly summary generated for team %s (week %s) — %d chars",
        team_id, week_start_date, len(summary_text),
    )
    return summary_text


# ---------------------------------------------------------------------------
# Public: APScheduler job entry point (all teams)
# ---------------------------------------------------------------------------

async def generate_all_team_summaries(
    team_repo,      # Member 1 repo — has .get_all_teams() and .get_week_data()
    summary_repo,   # Member 1 repo — has .upsert_summary()
) -> None:
    """
    APScheduler entry point.  Called every Sunday at 23:00 UTC.

    Iterates over all active teams, fetches the week's data from Member 1's
    repositories, and calls generate_team_summary() for each.
    """
    week_start = _get_current_week_start()
    logger.info("Starting weekly summary job for week %s", week_start)

    teams = await team_repo.get_all_teams()
    generated = 0

    for team in teams:
        try:
            week_data = await team_repo.get_week_data(
                team_id=str(team["id"]),
                week_start=week_start,
            )
            # week_data structure (provided by Member 1):
            # {
            #   "employee_summaries": [...],
            #   "risk_rows": [...],
            #   "blocker_stats": {...}
            # }
            result = await generate_team_summary(
                team_id=str(team["id"]),
                team_name=team["name"],
                week_start_date=week_start,
                employee_summaries=week_data.get("employee_summaries", []),
                risk_rows=week_data.get("risk_rows", []),
                blocker_stats=week_data.get("blocker_stats", {"opened": 0, "resolved": 0, "still_open": 0}),
                summary_repo=summary_repo,
            )
            if result:
                generated += 1
        except Exception as exc:
            logger.error("Summary failed for team %s: %s", team.get("id"), exc)

    logger.info(
        "Weekly summary job complete — %d/%d teams summarised",
        generated, len(teams),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_current_week_start() -> date:
    """Return the Monday of the current week."""
    today = date.today()
    return today - timedelta(days=today.weekday())


def _format_week_label(week_start: date) -> str:
    """Return e.g. 'Jan 8–12, 2024'"""
    week_end = week_start + timedelta(days=4)
    if week_start.month == week_end.month:
        return f"{week_start.strftime('%b')} {week_start.day}–{week_end.day}, {week_start.year}"
    return (
        f"{week_start.strftime('%b')} {week_start.day} – "
        f"{week_end.strftime('%b')} {week_end.day}, {week_start.year}"
    )