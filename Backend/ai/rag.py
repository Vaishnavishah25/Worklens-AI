"""
ai/rag.py  — Member 3
Full Retrieval-Augmented Generation pipeline.

Flow:
  1. embed_text(question)  → query vector
  2. faiss_store.search()  → top-20 results
  3. filter by team_id
  4. recency rerank        → top-8
  5. hydrate text from metadata (already stored inside FAISS metadata)
  6. fetch PostgreSQL risk data via Member 1 repo hook
  7. build context string + messages
  8. stream through LLM
"""

from __future__ import annotations

import math
import logging
from datetime import date, datetime
from typing import AsyncIterator

from ai.embedder import embed_text
from ai.prompts import build_chat_messages, build_context_string, build_recommendations_messages

from sqlalchemy import select, func

from database.session import SessionLocal
from database.models.user import User
from database.models.daily_update import DailyUpdate
from database.models.blocker import Blocker


from ai.llm import stream_chat, complete
from vectorstore.faiss_store import faiss_store

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuning constants (match spec)
# ---------------------------------------------------------------------------
FAISS_OVERFETCH_K = 20
TOP_K_AFTER_RERANK = 8
DECAY_LAMBDA = 0.1          # half-life ≈ 7 days


# ---------------------------------------------------------------------------
# Public entry point — used by api/v1/ai.py
# ---------------------------------------------------------------------------

async def retrieve_context(
    question: str,
    team_id: str,
    risk_json: list[dict],
) -> tuple[list[dict], str]:

    """
    Runs steps 1-6 of the RAG pipeline.

    Returns:
        (top_chunks, context_text)
        top_chunks  — list of enriched metadata dicts (for source citations)
        context_text — formatted string ready to inject into the prompt
    """
    # Step 1 — build DB-grounded context first (fixes Priya/Ankit bleed)
    # Heuristic: match employee names mentioned in the question.
    # If we can find any DB-grounded rows, we use them as primary context.

    db_context_text = ""
    db_top_chunks: list[dict] = []

    try:
        with SessionLocal() as session:
            users = session.execute(select(User)).scalars().all()
            question_l = question.lower()
            matched = [u for u in users if u.name and u.name.lower().split()[0] in question_l]

            # No employee named in the question ("who needs my attention?") →
            # ground the answer in recent activity across the whole roster
            # instead of falling through to the (currently stale) FAISS index.
            if not matched:
                matched = [u for u in users if u.role == "Employee"]

            if matched:
                matched_ids = [int(u.id) for u in matched]

                # Recent daily updates per matched employee (up to 4 each)
                updates = (
                    session.execute(
                        select(DailyUpdate)
                        .where(DailyUpdate.user_id.in_(matched_ids))
                        .order_by(DailyUpdate.created_at.desc())
                        .limit(16)
                    )
                    .scalars()
                    .all()
                )

                # Open blockers per matched employee
                blockers = (
                    session.execute(
                        select(Blocker)
                        .where(Blocker.user_id.in_(matched_ids), Blocker.status == "open")
                        .order_by(Blocker.created_at.desc())
                        .limit(32)
                    )
                    .scalars()
                    .all()
                )

                blocker_by_emp: dict[int, list[Blocker]] = {}
                for b in blockers:
                    blocker_by_emp.setdefault(int(b.user_id), []).append(b)

                # Build synthetic chunk dicts compatible with build_context_string()
                # build_context_string expects dicts with at least: full_name, date, doc_type, text
                for u in matched:
                    role_desc = u.role
                    if getattr(u, "title", None):
                        role_desc += f" ({u.title})"
                    db_top_chunks.append({
                        "doc_id": f"profile_{u.id}",
                        "doc_type": "profile",
                        "full_name": u.name,
                        "date": str(date.today()),
                        "text": f"[{u.name}] Role: {role_desc}.",
                        "similarity": 1.0,
                    })
                    u_updates = [du for du in updates if int(du.user_id) == int(u.id)][:4]
                    u_blockers = blocker_by_emp.get(int(u.id), [])[:3]

                    for du in u_updates:
                        btxt = ""
                        if u_blockers:
                            btxt = "\n".join([
                                f"- {bb.description} (sev {bb.severity})" for bb in u_blockers
                            ])

                        text = (
                            f"[{u.name}] {du.created_at.date()}: {du.work_done}. "
                            f"Next: {du.planned_work}. Confidence: {du.confidence_score}/10."
                        )
                        if btxt:
                            text += f"\nOpen blockers:\n{btxt}"

                        db_top_chunks.append(
                            {
                                "doc_id": f"db_update_{du.id}",
                                "doc_type": "db_daily_update",
                                "full_name": u.name,
                                "date": str(du.created_at.date()),
                                "text": text,
                                "similarity": 1.0,
                            }
                        )

                if db_top_chunks:
                    db_context_text = build_context_string(db_top_chunks)
    except Exception as exc:
        logger.error("DB grounding failed: %s", exc)

    # Step 2 — If we found DB-grounded rows, use them as primary context.
    if db_top_chunks:
        # Still return FAISS chunks for citations only if they exist.
        return db_top_chunks, db_context_text

    # Step 3 — FAISS search (fallback)
    query_vec = await embed_text(question)
    raw_results = faiss_store.search(query_vec, k=FAISS_OVERFETCH_K)

    # Step 4 — filter to this team only (when FAISS metadata has team_id)
    filtered = [r for r in raw_results if r.get("team_id") == str(team_id)]
    if not filtered:
        filtered = faiss_store.get_metadata_by_team_id(team_id)
        for r in filtered:
            r.setdefault("similarity", 0.0)

    # Step 5 — recency rerank
    reranked = _rerank(filtered, question)
    top_chunks = reranked[:TOP_K_AFTER_RERANK]


    # Step 5 — text is already in metadata["text"]
    # (indexer.py stores the serialised text alongside the vector)
    # Hydrate means confirm text exists; fall back to doc_id if somehow missing.
    for chunk in top_chunks:
        if "text" not in chunk:
            chunk["text"] = f"[{chunk['doc_type']}] {chunk['doc_id']}"

    # Step 6 — build context string
    context_text = build_context_string(top_chunks)

    return top_chunks, context_text

_PROFILE_KEYWORDS = {"role", "title", "position", "designation", "manager", "department"}

def _maybe_answer_profile_question(question: str, matched: list) -> str | None:
    """Answer 'what is X's role' directly from the User row instead of
    routing it through the update/blocker pipeline, which has no role data
    and — on the offline fallback — no way to recognize an off-topic question."""
    if not any(kw in question.lower() for kw in _PROFILE_KEYWORDS):
        return None
    if len(matched) != 1:
        return None  # ambiguous — let the normal pipeline handle it
    u = matched[0]
    title = f" ({u.title})" if getattr(u, "title", None) else ""
    return f"{u.name} is a {u.role}{title}."
async def stream_rag_response(
    question: str,
    team_id: str,
    risk_json: list[dict],
) -> AsyncIterator[dict]:
    """
    Full RAG pipeline — yields SSE-ready dicts.

    Yields:
        {"type": "chunk", "text": "..."}   — one per streaming token
        {"type": "done",  "sources": [...]} — final event with citations
    """
    try:
        with SessionLocal() as session:
            users = session.execute(select(User)).scalars().all()
            matched = [u for u in users if u.name and u.name.lower().split()[0] in question.lower()]
        direct = _maybe_answer_profile_question(question, matched)
        if direct:
            yield {"type": "chunk", "text": direct}
            yield {"type": "done", "sources": [], "full_response": direct}
            return
    except Exception as exc:
        logger.error("Profile short-circuit failed: %s", exc)
        # fall through to the normal pipeline below on any failure
    top_chunks, context_text = await retrieve_context(question, team_id, risk_json)
    messages = build_chat_messages(question, context_text, risk_json)

    full_response = ""
    try:
        async for delta in stream_chat(messages):
            if delta:
                full_response += delta
                yield {"type": "chunk", "text": delta}
    except Exception as exc:
        logger.error("LLM streaming error: %s", exc)
        yield {"type": "error", "text": "AI service error. Please try again."}
        return

    # Final event — source citations
    sources = [
        {
            "employee": c.get("full_name", "Unknown"),
            "date": c.get("date", ""),
            "doc_type": c.get("doc_type", ""),
        }
        for c in top_chunks
    ]
    yield {"type": "done", "sources": sources, "full_response": full_response}


async def generate_recommendations(
    team_id: str,
    risk_json: list[dict],
) -> list[dict]:
    """
    Non-streaming: generate 3-5 JSON action items for the manager.
    Returns a list of recommendation dicts or empty list on failure.
    """
    import json as _json

    # Grab recent context for this team
    query_vec = await embed_text("team blockers risks overdue tasks confidence low")
    raw_results = faiss_store.search(query_vec, k=10)
    filtered = [r for r in raw_results if r.get("team_id") == str(team_id)]
    if not filtered:
        filtered = faiss_store.get_metadata_by_team_id(team_id)
        for r in filtered:
            r.setdefault("similarity", 0.0)
    reranked = _rerank(filtered, "team blockers risks overdue tasks confidence low")[:8]
    context_text = build_context_string(reranked)

    messages = build_recommendations_messages(context_text, risk_json)
    raw = await complete(messages, max_tokens=600)

    # Strip markdown fences if the model includes them
    clean = raw.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0]

    try:
        return _json.loads(clean.strip())
    except _json.JSONDecodeError as exc:
        logger.error("Failed to parse recommendations JSON: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Recency reranking (spec formula)
# ---------------------------------------------------------------------------

def _rerank(results: list[dict], question: str = "") -> list[dict]:
    """
    final_score = similarity × e^(-λ × delta_t_days)
    Sorts descending so the best results come first.
    """
    today = date.today()
    scored: list[tuple[float, dict]] = []

    query_terms = {
        term
        for term in question.lower().replace("?", " ").split()
        if len(term) > 2
    }

    for r in results:
        raw_date = r.get("date", str(today))
        try:
            doc_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
        except ValueError:
            doc_date = today
        delta_t = (today - doc_date).days
        sim = r.get("similarity", 0.0)
        searchable_text = " ".join(
            str(r.get(key, "")).lower()
            for key in ("full_name", "doc_type", "text")
        )
        lexical_hits = sum(1 for term in query_terms if term in searchable_text)
        final_score = (sim + (0.05 * lexical_hits)) * math.exp(-DECAY_LAMBDA * delta_t)
        scored.append((final_score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]