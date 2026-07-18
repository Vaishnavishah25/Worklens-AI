"""
test/test_indexer.py
Tests vectorstore/indexer.py — run with: python -m pytest test/test_indexer.py -v
Requires Ollama running (uses real embed_text call).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Backend', 'app'))

import pytest
from vectorstore.indexer import index_update, index_blocker, index_feedback
from vectorstore.faiss_store import faiss_store


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_UPDATE = {
    "id": "test-update-001",
    "employee_id": "emp-001",
    "team_id": "team-001",
    "full_name": "Priya Sharma",
    "date": "2024-01-15",
    "work_done": "Fixed OAuth callback bug and wrote 14 unit tests.",
    "next_steps": "Finish refresh token flow and review Ravi's PR.",
    "confidence_score": 7,
    "mood": 4,
    "blocker_description": None,
}

SAMPLE_UPDATE_WITH_BLOCKER = {
    "id": "test-update-002",
    "employee_id": "emp-001",
    "team_id": "team-001",
    "full_name": "Priya Sharma",
    "date": "2024-01-14",
    "work_done": "Minor code cleanup while waiting for DevOps.",
    "next_steps": "Wait for staging env, then complete auth flow.",
    "confidence_score": 5,
    "mood": 2,
    "blocker_description": "Staging environment not provisioned by DevOps team.",
}

SAMPLE_BLOCKER = {
    "id": "test-blocker-001",
    "employee_id": "emp-001",
    "team_id": "team-001",
    "full_name": "Priya Sharma",
    "date": "2024-01-12",
    "description": "Staging environment not provisioned by DevOps team.",
    "severity": 2,
    "status": "open",
}

SAMPLE_FEEDBACK = {
    "id": "test-feedback-001",
    "to_employee_id": "emp-002",
    "team_id": "team-001",
    "from_name": "Kavitha R.",
    "to_name": "Ankit Mehta",
    "type": "praise",
    "content": "Strong PR review quality this week. Your comments are constructive.",
    "date": "2024-01-13",
}


# ── index_update tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_index_update_returns_doc_id():
    doc_id = await index_update(SAMPLE_UPDATE)
    assert doc_id is not None
    assert doc_id == "update_test-update-001"
    print(f"\nINDEX UPDATE: doc_id={doc_id}")


@pytest.mark.asyncio
async def test_index_update_adds_to_faiss():
    before = faiss_store.total_vectors
    await index_update(SAMPLE_UPDATE)
    after = faiss_store.total_vectors
    assert after > before
    print(f"\nFAISS VECTORS: {before} → {after}")


@pytest.mark.asyncio
async def test_index_update_with_blocker():
    doc_id = await index_update(SAMPLE_UPDATE_WITH_BLOCKER)
    assert doc_id == "update_test-update-002"
    print(f"\nINDEX UPDATE WITH BLOCKER: {doc_id}")


@pytest.mark.asyncio
async def test_index_update_metadata_stored():
    await index_update(SAMPLE_UPDATE)
    meta = faiss_store.get_metadata_by_doc_id("update_test-update-001")
    assert meta is not None
    assert meta["full_name"] == "Priya Sharma"
    assert meta["team_id"] == "team-001"
    assert meta["doc_type"] == "daily_update"
    assert "text" in meta
    print(f"\nMETADATA STORED:")
    print(f"  full_name : {meta['full_name']}")
    print(f"  doc_type  : {meta['doc_type']}")
    print(f"  text      : {meta['text'][:60]}...")


# ── index_blocker tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_index_blocker_returns_doc_id():
    doc_id = await index_blocker(SAMPLE_BLOCKER)
    assert doc_id == "blocker_test-blocker-001"
    print(f"\nINDEX BLOCKER: doc_id={doc_id}")


@pytest.mark.asyncio
async def test_index_blocker_metadata():
    await index_blocker(SAMPLE_BLOCKER)
    meta = faiss_store.get_metadata_by_doc_id("blocker_test-blocker-001")
    assert meta is not None
    assert meta["doc_type"] == "blocker"
    assert meta["severity"] == 2
    print(f"\nBLOCKER METADATA: severity={meta['severity']} type={meta['doc_type']}")


# ── index_feedback tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_index_feedback_returns_doc_id():
    doc_id = await index_feedback(SAMPLE_FEEDBACK)
    assert doc_id == "feedback_test-feedback-001"
    print(f"\nINDEX FEEDBACK: doc_id={doc_id}")


@pytest.mark.asyncio
async def test_index_feedback_metadata():
    await index_feedback(SAMPLE_FEEDBACK)
    meta = faiss_store.get_metadata_by_doc_id("feedback_test-feedback-001")
    assert meta is not None
    assert meta["doc_type"] == "feedback"
    assert meta["feedback_type"] == "praise"
    assert meta["full_name"] == "Ankit Mehta"
    print(f"\nFEEDBACK METADATA: type={meta['feedback_type']} to={meta['full_name']}")


# ── Search after indexing ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_indexed_update_is_searchable():
    """After indexing, a related query should find the document."""
    from ai.embedder import embed_text

    await index_update(SAMPLE_UPDATE)
    query_vec = await embed_text("OAuth authentication bug fix unit tests")
    results = faiss_store.search(query_vec, k=5)

    doc_ids = [r["doc_id"] for r in results]
    print(f"\nSEARCH RESULTS for 'OAuth bug fix': {doc_ids}")
    assert any("update" in d for d in doc_ids), "Update should appear in search results"