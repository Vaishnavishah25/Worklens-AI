# backend/repositories/summary_repository.py

from __future__ import annotations
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        db: Optional[AsyncSession] = None,
    ) -> None:
        if db is not None:
            await self._execute_upsert(db, team_id, week_start_date, summary, no_data, generated_at)
        else:
            async with SessionLocal() as session:
                await self._execute_upsert(session, team_id, week_start_date, summary, no_data, generated_at)

    async def _execute_upsert(
        self,
        session: AsyncSession,
        team_id: str,
        week_start_date: str,
        summary: str | None,
        no_data: bool,
        generated_at,
    ) -> None:
        result = await session.execute(
            select(WeeklySummary).where(
                WeeklySummary.team_id == str(team_id),
                WeeklySummary.week_start_date == str(week_start_date),
            )
        )
        row = result.scalar_one_or_none()

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

        await session.commit()

    async def get_summary(
        self,
        team_id: str,
        week_start_date: str,
        db: Optional[AsyncSession] = None,
    ) -> dict | None:
        if db is not None:
            return await self._execute_get(db, team_id, week_start_date)
        else:
            async with SessionLocal() as session:
                return await self._execute_get(session, team_id, week_start_date)

    async def _execute_get(
        self,
        session: AsyncSession,
        team_id: str,
        week_start_date: str,
    ) -> dict | None:
        result = await session.execute(
            select(WeeklySummary).where(
                WeeklySummary.team_id == str(team_id),
                WeeklySummary.week_start_date == str(week_start_date),
            )
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return {
            "summary": row.summary,
            "no_data": row.no_data,
            "generated_at": row.generated_at,
        }