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
    full_name = update.get("full_name", "Employee")
    date_val = update.get("date", update.get("created_at", "Today"))
    work_done = update.get("work_done", "No summary provided")
    next_steps = update.get("next_steps", "N/A")
    confidence = update.get("confidence_score", 5)
    blocker_text = update.get("blocker_description") or "None"

    return (
        f"[{full_name}] {date_val}: "
        f"{work_done}. "
        f"Blockers: {blocker_text}. "
        f"Next: {next_steps}. "
        f"Confidence: {confidence}/10. "
    )


def serialise_blocker(blocker: dict) -> str:
    severity = blocker.get("severity", "MEDIUM")
    full_name = blocker.get("full_name", "Employee")
    date_val = blocker.get("date", blocker.get("created_at", "Today"))
    description = blocker.get("description", "No description")
    status = blocker.get("status", "open")

    return (
        f"BLOCKER [{severity}] [{full_name}] "
        f"{date_val}: {description}. "
        f"Status: {status}."
    )


def serialise_feedback(feedback: dict) -> str:
    fb_type = str(feedback.get("type", "guidance")).upper()
    from_name = feedback.get("from_name", "Mentor")
    to_name = feedback.get("to_name", "Mentee")
    content = feedback.get("content", feedback.get("message", ""))

    return (
        f"FEEDBACK [{fb_type}] "
        f"from {from_name} to {to_name}: "
        f"{content}."
    )
