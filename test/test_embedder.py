"""
test/test_embedder.py
Tests ai/embedder.py — run with: python -m pytest test/test_embedder.py -v
Requires Ollama running at localhost:11434 with nomic-embed-text pulled.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Backend', 'app'))

import pytest
import asyncio
import numpy as np
from ai.embedder import (
    embed_text,
    embed_texts,
    serialise_daily_update,
    serialise_blocker,
    serialise_feedback,
    EMBEDDING_DIMS,
)


# ── Serialiser tests (no network needed) ─────────────────────────────────────

def test_serialise_daily_update_all_fields():
    update = {
        "full_name": "Priya Sharma",
        "date": "2024-01-15",
        "work_done": "Fixed OAuth callback bug",
        "next_steps": "Write unit tests",
        "confidence_score": 8,
        "mood": 4,
        "blocker_description": "Staging env not ready",
    }
    result = serialise_daily_update(update)
    assert "Priya Sharma" in result
    assert "Fixed OAuth callback bug" in result
    assert "Staging env not ready" in result
    assert "8/10" in result
    print(f"\nSERIALISED UPDATE:\n{result}")


def test_serialise_daily_update_no_blocker():
    update = {
        "full_name": "Ravi Kumar",
        "date": "2024-01-15",
        "work_done": "Merged PR #47",
        "next_steps": "Start new feature",
        "confidence_score": 7,
    }
    result = serialise_daily_update(update)
    assert "None" in result          # blocker should say None
    assert "Ravi Kumar" in result
    print(f"\nSERIALISED UPDATE (no blocker):\n{result}")


def test_serialise_blocker():
    blocker = {
        "full_name": "Priya Sharma",
        "date": "2024-01-12",
        "description": "Staging env not provisioned by DevOps",
        "severity": 2,
        "status": "open",
    }
    result = serialise_blocker(blocker)
    assert "BLOCKER" in result
    assert "[2]" in result
    assert "Priya Sharma" in result
    print(f"\nSERIALISED BLOCKER:\n{result}")


def test_serialise_feedback():
    feedback = {
        "from_name": "Kavitha R.",
        "to_name": "Ankit Mehta",
        "type": "praise",
        "content": "Strong PR review quality this week.",
    }
    result = serialise_feedback(feedback)
    assert "FEEDBACK" in result
    assert "PRAISE" in result
    assert "Kavitha R." in result
    print(f"\nSERIALISED FEEDBACK:\n{result}")


# ── Embedding tests (needs Ollama running) ────────────────────────────────────

@pytest.mark.asyncio
async def test_embed_text_returns_correct_shape():
    vector = await embed_text("Employee worked on authentication module today.")
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (EMBEDDING_DIMS,)
    assert vector.dtype == np.float32
    print(f"\nEMBEDDING SHAPE: {vector.shape}")
    print(f"FIRST 5 VALUES: {vector[:5]}")


@pytest.mark.asyncio
async def test_embed_text_is_normalised():
    vector = await embed_text("Test normalisation of embedding vector.")
    norm = np.linalg.norm(vector)
    assert abs(norm - 1.0) < 0.001, f"Expected norm ~1.0, got {norm}"
    print(f"\nVECTOR NORM: {norm:.6f} (should be ~1.0)")


@pytest.mark.asyncio
async def test_embed_texts_batch():
    texts = [
        "Fixed a bug in the auth module",
        "Worked on database migrations",
        "Reviewed pull requests",
    ]
    vectors = await embed_texts(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert v.shape == (EMBEDDING_DIMS,)
    print(f"\nBATCH EMBEDDING: {len(vectors)} vectors of shape {vectors[0].shape}")


@pytest.mark.asyncio
async def test_similar_texts_have_higher_similarity():
    v1 = await embed_text("worked on authentication and login feature")
    v2 = await embed_text("implemented login and auth system")
    v3 = await embed_text("fixed CSS styling on the dashboard page")

    sim_related = float(np.dot(v1, v2))
    sim_unrelated = float(np.dot(v1, v3))

    print(f"\nSIMILARITY (related):   {sim_related:.4f}")
    print(f"SIMILARITY (unrelated): {sim_unrelated:.4f}")
    assert sim_related > sim_unrelated, "Related texts should be more similar"


@pytest.mark.asyncio
async def test_embed_daily_update_full_pipeline():
    update = {
        "full_name": "Priya Sharma",
        "date": "2024-01-15",
        "work_done": "Fixed OAuth callback bug, wrote unit tests",
        "next_steps": "Finish refresh token flow",
        "confidence_score": 7,
        "mood": 4,
        "blocker_description": None,
    }
    text = serialise_daily_update(update)
    vector = await embed_text(text)
    assert vector.shape == (EMBEDDING_DIMS,)
    print(f"\nFULL PIPELINE TEST PASSED")
    print(f"TEXT: {text[:80]}...")
    print(f"VECTOR SHAPE: {vector.shape}")