"""
repositories/summary_repository.py

Persists weekly AI-generated team summaries to worklens.db.
Used by api/v1/ai.py (/ai/summarize and /ai/summary routes) via
services/summary_service.py's summary_repo parameter.
"""

from __future__ import annotations

from models.weekly_summary import WeeklySummary
from database.session import SessionLocal


class SummaryRepository:

    async def upsert_summary(
        self,
        team_id: str,
        week_start_date: str,
        summary: str | None,
        no_data: bool,
        generated_at,
    ) -> None:

        with SessionLocal() as session:
            row = (
                session.query(WeeklySummary)
                .filter(
                    WeeklySummary.team_id == str(team_id),
                    WeeklySummary.week_start_date == str(week_start_date),
                )
                .first()
            )

            if row:
                row.summary = summary
                row.no_data = no_data
                row.generated_at = generated_at
            else:
                row = WeeklySummary(
                    team_id=str(team_id),
                    week_start_date=str(week_start_date),
                    summary=summary,
                    no_data=no_data,
                    generated_at=generated_at,
                )
                session.add(row)

            session.commit()

    async def get_summary(
        self,
        team_id: str,
        week_start_date: str,
    ) -> dict | None:

        with SessionLocal() as session:
            row = (
                session.query(WeeklySummary)
                .filter(
                    WeeklySummary.team_id == str(team_id),
                    WeeklySummary.week_start_date == str(week_start_date),
                )
                .first()
            )

            if row is None:
                return None

            return {
                "summary": row.summary,
                "no_data": row.no_data,
                "generated_at": row.generated_at,
            }