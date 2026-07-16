"""
vectorstore/faiss_store.py  — Member 3
In-process FAISS IndexFlatIP (inner-product = cosine after L2-norm).
Stores vectors + metadata in memory; persists to disk on demand.

SINGLE-WORKER WARNING:
  This store is NOT thread-safe for concurrent writes.
  Run Uvicorn with --workers 1.
  A threading.Lock() serialises all writes from the main thread
  and any BackgroundTask coroutines.
"""

from __future__ import annotations

import os
import json
import threading
import logging
from pathlib import Path

import numpy as np
import faiss

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EMBEDDING_DIMS = 768
# Where to save the persisted index on disk.
# Anchor defaults to Backend/app so seeding and API startup use the same files
# even when they are launched from different working directories.
APP_DIR = Path(__file__).resolve().parents[1]


def _app_relative_path(env_name: str, default: Path) -> Path:
    configured = Path(os.getenv(env_name, str(default)))
    if configured.is_absolute():
        return configured
    return APP_DIR / configured


INDEX_PATH = _app_relative_path("FAISS_INDEX_PATH", APP_DIR / "vectorstore" / "faiss.index")
META_PATH = _app_relative_path("FAISS_META_PATH", APP_DIR / "vectorstore" / "faiss_meta.json")


# ---------------------------------------------------------------------------
# FAISSStore — singleton
# ---------------------------------------------------------------------------

class FAISSStore:
    """
    Wraps a faiss.IndexFlatIP.
    Metadata (employee_id, team_id, date, doc_type, doc_id) is stored in a
    parallel Python list because FAISS only stores float32 vectors.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBEDDING_DIMS)
        # metadata[i] corresponds to _index vector at position i
        self._metadata: list[dict] = []
        self._load_if_exists()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add(self, vector: np.ndarray, metadata: dict) -> int:
        """
        Add a single L2-normalised vector with its metadata dict.

        Required metadata keys:
            doc_id, employee_id, team_id, date (str YYYY-MM-DD), doc_type

        Returns the FAISS integer index of the added vector.
        """
        vec = self._ensure_shape(vector)
        with self._lock:
            self._index.add(vec)
            position = len(self._metadata)
            self._metadata.append(metadata)
        return position

    def add_batch(self, vectors: list[np.ndarray], metadatas: list[dict]) -> None:
        """Add multiple vectors at once (slightly faster than looping add())."""
        matrix = np.vstack([self._ensure_shape(v) for v in vectors])
        with self._lock:
            self._index.add(matrix)
            self._metadata.extend(metadatas)

    # ------------------------------------------------------------------
    # Read / search
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 20,
    ) -> list[dict]:
        """
        Return top-k results as a list of metadata dicts enriched with a
        'similarity' float (0–1).

        Uses IndexFlatIP so similarity = dot product ≈ cosine similarity
        (because all stored vectors are L2-normalised).
        """
        if self._index.ntotal == 0:
            return []

        vec = self._ensure_shape(query_vector)
        k = min(k, self._index.ntotal)

        with self._lock:
            distances, indices = self._index.search(vec, k)

        results: list[dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = dict(self._metadata[idx])   # shallow copy
            meta["similarity"] = float(dist)   # inner product = cosine sim
            results.append(meta)

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist index + metadata to disk."""
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            faiss.write_index(self._index, str(INDEX_PATH))
            META_PATH.write_text(json.dumps(self._metadata, default=str))
        logger.info("FAISS index saved — %d vectors", self._index.ntotal)

    def _load_if_exists(self) -> None:
        if INDEX_PATH.exists() and META_PATH.exists():
            try:
                self._index = faiss.read_index(str(INDEX_PATH))
                self._metadata = json.loads(META_PATH.read_text())
                logger.info(
                    "FAISS index loaded — %d vectors", self._index.ntotal
                )
            except Exception as exc:          # corrupted file — start fresh
                logger.warning("Could not load FAISS index: %s", exc)
                self._index = faiss.IndexFlatIP(EMBEDDING_DIMS)
                self._metadata = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_shape(vector: np.ndarray) -> np.ndarray:
        """Make sure the vector is float32 and shaped (1, DIMS) for FAISS."""
        v = vector.astype(np.float32)
        if v.ndim == 1:
            v = v.reshape(1, -1)
        return v

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal

    def get_metadata_by_doc_id(self, doc_id: str) -> dict | None:
        for m in self._metadata:
            if m.get("doc_id") == doc_id:
                return m
        return None

    def get_metadata_by_team_id(self, team_id: str) -> list[dict]:
        """Return stored metadata rows for one team without using vector search."""
        with self._lock:
            return [dict(m) for m in self._metadata if m.get("team_id") == str(team_id)]


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
faiss_store = FAISSStore()
