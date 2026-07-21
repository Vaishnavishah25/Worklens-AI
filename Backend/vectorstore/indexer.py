"""
vectorstore/indexer.py  — Member 3
Background task called by Member 1's update_service.py after every DB write.

Integration contract (DO NOT CHANGE SIGNATURES):
    await index_update(db_update)   ← called from services/update_service.py
    await index_blocker(db_blocker) ← called from services/blocker_service.py
    await index_feedback(db_feedback) ← called from services/feedback_service.py
    await backfill_missing()        ← called by the nightly APScheduler job
"""

from __future__ import annotations

import logging
from datetime import date

from ai.embedder import (
    embed_text,
    serialise_daily_update,
    serialise_blocker,
    serialise_feedback,
)
from vectorstore.faiss_store import faiss_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public integration hooks
# ---------------------------------------------------------------------------

async def index_update(db_update: dict) -> str | None:
    """
    Embed a daily_update row and store it in FAISS.

    Expected keys in db_update:
        id (str UUID), employee_id, team_id, full_name,
        date (str YYYY-MM-DD), work_done, next_steps,
        confidence_score, mood (optional),
        blocker_description (optional — from joined blocker row)

    Returns the FAISS metadata doc_id on success, None on failure.
    """
    doc_id = f"update_{db_update.get('id')}"
    try:
        text = serialise_daily_update(db_update)
        vector = await embed_text(text)

        metadata = {
            "doc_id": doc_id,
            "employee_id": str(db_update.get("employee_id", "")),
            "team_id": str(db_update.get("team_id", "")),
            "full_name": db_update.get("full_name", ""),
            "date": str(db_update.get("date", date.today())),
            "doc_type": "daily_update",
            "text": text,
        }

        faiss_store.add(vector, metadata)
        logger.info("Indexed daily_update %s for %s", doc_id, db_update["full_name"])
        return doc_id

    except Exception as exc:
        logger.error("Failed to index update %s: %s", doc_id, exc)
        return None


async def index_blocker(db_blocker: dict) -> str | None:
    """
    Embed a blocker row and store it in FAISS.

    Expected keys:
        id, employee_id, team_id, full_name,
        date (created_at date), description,
        severity (1-3), status
    """
    doc_id = f"blocker_{db_blocker.get('id')}"
    try:
        text = serialise_blocker(db_blocker)
        vector = await embed_text(text)

        metadata = {
            "doc_id": doc_id,
            "employee_id": str(db_blocker.get("employee_id", "")),
            "team_id": str(db_blocker.get("team_id", "")),
            "full_name": db_blocker.get("full_name", ""),
            "date": str(db_blocker.get("date", date.today())),
            "doc_type": "blocker",
            "severity": db_blocker.get("severity", "MEDIUM"),
            "text": text,
        }

        faiss_store.add(vector, metadata)
        logger.info("Indexed blocker %s", doc_id)
        return doc_id

    except Exception as exc:
        logger.error("Failed to index blocker %s: %s", doc_id, exc)
        return None


async def index_feedback(db_feedback: dict) -> str | None:
    """
    Embed a feedback row and store it in FAISS.

    Expected keys:
        id, to_employee_id, team_id,
        from_name, to_name, type (praise/guidance/concern),
        content, date
    """
    doc_id = f"feedback_{db_feedback.get('id')}"
    try:
        text = serialise_feedback(db_feedback)
        vector = await embed_text(text)

        metadata = {
            "doc_id": doc_id,
            "employee_id": str(db_feedback.get("to_employee_id", "")),
            "team_id": str(db_feedback.get("team_id", "")),
            "full_name": db_feedback.get("to_name", ""),
            "date": str(db_feedback.get("date", date.today())),
            "doc_type": "feedback",
            "feedback_type": db_feedback.get("type", "guidance"),
            "text": text,
        }

        faiss_store.add(vector, metadata)
        logger.info("Indexed feedback %s", doc_id)
        return doc_id

    except Exception as exc:
        logger.error("Failed to index feedback %s: %s", doc_id, exc)
        return None


# ---------------------------------------------------------------------------
# Nightly backfill job
# ---------------------------------------------------------------------------

async def backfill_missing(missing_updates: list[dict], missing_blockers: list[dict]) -> None:
    """
    Called by the APScheduler 'faiss_backfill' job at 02:00 UTC.
    Re-attempts embedding for rows where embedding_id IS NULL in PostgreSQL.

    Member 1 passes in the rows with missing embeddings; we embed them and
    call faiss_store.save() at the end to persist the updated index.

    Args:
        missing_updates:  List of db_update dicts with embedding_id=None
        missing_blockers: List of db_blocker dicts with embedding_id=None
    """
    indexed = 0

    for update in missing_updates:
        result = await index_update(update)
        if result:
            indexed += 1

    for blocker in missing_blockers:
        result = await index_blocker(blocker)
        if result:
            indexed += 1

    if indexed:
        faiss_store.save()
        logger.info("Backfill complete — indexed %d documents", indexed)
    else:
        logger.info("Backfill: no missing documents found")