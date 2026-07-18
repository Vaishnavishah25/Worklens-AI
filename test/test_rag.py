"""
test/test_rag.py
Tests ai/rag.py — run with: python -m pytest test/test_rag.py -v
Requires Ollama running with both models pulled.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Backend', 'app'))

import asyncio
import pytest
from vectorstore.indexer import index_update, index_blocker
from ai.rag import retrieve_context, stream_rag_response, _rerank
from datetime import date, timedelta


TEAM_ID = "team-rag-test"

SAMPLE_UPDATES = [
    {
        "id": f"rag-update-{i}",
        "employee_id": "emp-001",
        "team_id": TEAM_ID,
        "full_name": "Priya Sharma",
        "date": str(date.today() - timedelta(days=i)),
        "work_done": f"Day {i}: Worked on OAuth authentication module.",
        "next_steps": "Continue auth work.",
        "confidence_score": 8 - i,
        "mood": 4,
        "blocker_description": "Staging env not ready" if i == 2 else None,
    }
    for i in range(3)
]

SAMPLE_BLOCKER = {
    "id": "rag-blocker-001",
    "employee_id": "emp-001",
    "team_id": TEAM_ID,
    "full_name": "Priya Sharma",
    "date": str(date.today() - timedelta(days=2)),
    "description": "Staging environment not provisioned by DevOps.",
    "severity": 2,
    "status": "open",
}

RISK_JSON = [
    {
        "employee_id": "emp-001",
        "full_name": "Priya Sharma",
        "score": 0.78,
        "label": "HIGH",
        "days_since_update": 0,
        "open_blockers": 1,
        "overdue_tasks": 1,
        "avg_confidence_7d": 6.0,
    }
]


# ── Setup — index some data before RAG tests ──────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def seed_faiss():
    """Index sample data once before all tests in this module."""
    async def _seed() -> None:
        for update in SAMPLE_UPDATES:
            await index_update(update)
        await index_blocker(SAMPLE_BLOCKER)

    asyncio.run(_seed())
    print(f"\nSEEDED FAISS with {len(SAMPLE_UPDATES)} updates + 1 blocker")


# ── Reranking unit test (no network) ─────────────────────────────────────────

def test_rerank_fresher_wins():
    today = date.today()
    results = [
        {"doc_id": "old",   "similarity": 0.95, "date": str(today - timedelta(days=10))},
        {"doc_id": "fresh", "similarity": 0.85, "date": str(today - timedelta(days=1))},
    ]
    reranked = _rerank(results)
    assert reranked[0]["doc_id"] == "fresh", "Fresher document should rank higher despite lower similarity"
    print(f"\nRERANK: fresh(0.85, 1d) beats old(0.95, 10d) — OK")


def test_rerank_very_old_drops():
    today = date.today()
    results = [
        {"doc_id": "ancient", "similarity": 1.0,  "date": str(today - timedelta(days=30))},
        {"doc_id": "recent",  "similarity": 0.5,  "date": str(today)},
    ]
    reranked = _rerank(results)
    assert reranked[0]["doc_id"] == "recent"
    print(f"\nRERANK: recent(0.5, 0d) beats ancient(1.0, 30d) — OK")


# ── retrieve_context ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retrieve_context_returns_chunks_and_text():
    chunks, context_text = await retrieve_context(
        question="Why is Priya blocked?",
        team_id=TEAM_ID,
        risk_json=RISK_JSON,
    )
    assert isinstance(chunks, list)
    assert isinstance(context_text, str)
    assert len(context_text) > 0
    print(f"\nRETRIEVE CONTEXT:")
    print(f"  chunks returned : {len(chunks)}")
    print(f"  context preview : {context_text[:120]}...")


@pytest.mark.asyncio
async def test_retrieve_context_filters_by_team():
    """Data from a different team should not appear in results."""
    chunks, _ = await retrieve_context(
        question="What did the team work on?",
        team_id="completely-different-team-id",
        risk_json=[],
    )
    for chunk in chunks:
        assert chunk.get("team_id") != TEAM_ID
    print(f"\nTEAM FILTER: {len(chunks)} chunks from other team — none from our seed data")


@pytest.mark.asyncio
async def test_retrieve_context_chunks_have_required_fields():
    chunks, _ = await retrieve_context(
        question="authentication blocker staging",
        team_id=TEAM_ID,
        risk_json=RISK_JSON,
    )
    for chunk in chunks:
        assert "doc_id" in chunk
        assert "full_name" in chunk
        assert "date" in chunk
        assert "similarity" in chunk
        assert "text" in chunk
    print(f"\nCHUNK FIELDS OK — {len(chunks)} chunks all have required keys")


# ── stream_rag_response ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_rag_yields_chunks():
    events = []
    async for event in stream_rag_response(
        question="What is Priya working on and is she blocked?",
        team_id=TEAM_ID,
        risk_json=RISK_JSON,
    ):
        events.append(event)

    types = [e["type"] for e in events]
    assert "chunk" in types,  "Should have text chunk events"
    assert "done"  in types,  "Should have a done event"
    print(f"\nSTREAM RAG EVENTS: {len(events)} total")
    print(f"  types seen: {set(types)}")


@pytest.mark.asyncio
async def test_stream_rag_full_response_not_empty():
    full_text = ""
    sources = []
    async for event in stream_rag_response(
        question="What is Priya working on?",
        team_id=TEAM_ID,
        risk_json=RISK_JSON,
    ):
        if event["type"] == "chunk":
            full_text += event.get("text", "")
        elif event["type"] == "done":
            sources = event.get("sources", [])

    assert len(full_text) > 20
    assert isinstance(sources, list)
    print(f"\nFULL RAG RESPONSE ({len(full_text)} chars):")
    print(f"  {full_text[:200]}...")
    print(f"SOURCES: {sources}")


@pytest.mark.asyncio
async def test_stream_rag_done_event_has_sources():
    done_event = None
    async for event in stream_rag_response(
        question="staging environment blocker",
        team_id=TEAM_ID,
        risk_json=RISK_JSON,
    ):
        if event["type"] == "done":
            done_event = event
            break

    assert done_event is not None
    assert "sources" in done_event
    print(f"\nDONE EVENT SOURCES: {done_event['sources']}")