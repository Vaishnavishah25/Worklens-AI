"""
ai/embedder.py  — Member 3  (Ollama version)
"""
from __future__ import annotations
import hashlib
import os
import re
import httpx
import numpy as np

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMS = 768   # nomic-embed-text is 768, not 1536
USE_OLLAMA = os.getenv("WORKLENS_USE_OLLAMA", "0") == "1"


def _fallback_embed_text(text: str) -> np.ndarray:
    """Create a deterministic, lightweight embedding when Ollama is unavailable."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    vector = np.zeros(EMBEDDING_DIMS, dtype=np.float32)
    if not cleaned:
        return vector

    tokens = cleaned.split()
    for token in tokens:
        digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % EMBEDDING_DIMS
        vector[index] += 1.0

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


async def embed_text(text: str) -> np.ndarray:
    text = text.strip().replace("\n", " ")
    if not USE_OLLAMA:
        return _fallback_embed_text(text)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=2.0,
            )
            response.raise_for_status()
            vector = np.array(response.json()["embedding"], dtype=np.float32)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
    except Exception:
        return _fallback_embed_text(text)


async def embed_texts(texts: list[str]) -> list[np.ndarray]:
    return [await embed_text(t) for t in texts]


def serialise_daily_update(update: dict) -> str:
    blocker_text = update.get("blocker_description") or "None"
    return (
        f"[{update['full_name']}] {update['date']}: "
        f"{update['work_done']}. "
        f"Blockers: {blocker_text}. "
        f"Next: {update['next_steps']}. "
        f"Confidence: {update['confidence_score']}/10. "
        f"Mood: {update.get('mood', 'N/A')}/5."
    )


def serialise_blocker(blocker: dict) -> str:
    return (
        f"BLOCKER [{blocker['severity']}] [{blocker['full_name']}] "
        f"{blocker['date']}: {blocker['description']}. "
        f"Status: {blocker['status']}."
    )


def serialise_feedback(feedback: dict) -> str:
    return (
        f"FEEDBACK [{feedback['type'].upper()}] "
        f"from {feedback['from_name']} to {feedback['to_name']}: "
        f"{feedback['content']}."
    )
