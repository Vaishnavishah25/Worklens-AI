"""
Backend/app/main.py
WorkLens AI — FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()                          # must be first — loads .env before anything else

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Routers that exist today ─────────────────────────────────────────────────
try:
    from api.v1.ai import router as ai_router
    from api.v1.auth import router as auth_router
    from vectorstore.faiss_store import faiss_store
except ModuleNotFoundError:
    from api.v1.ai import router as ai_router
    from api.v1.auth import router as auth_router
    from vectorstore.faiss_store import faiss_store

# ── Routers that do NOT exist yet in this repo ───────────────────────────────
# Uncomment each import (and the matching app.include_router call below) the
# moment the teammate building it actually commits the file. Importing these
# before the file exists will crash the app with ModuleNotFoundError.
# from api.v1.tasks      import router as tasks_router
# from api.v1.dashboard  import router as dashboard_router
# from api.v1.analytics  import router as analytics_router
# from api.v1.alerts     import router as alerts_router
# from api.v1.feedback   import router as feedback_router
# from api.v1.users      import router as employees_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    logger.info("WorkLens AI starting up…")
    logger.info("FAISS index loaded — %d vectors", faiss_store.total_vectors)

    try:
        from api.v1.auth import init_db, seed_default_users
    except ModuleNotFoundError:
        from api.v1.auth import init_db, seed_default_users

    init_db()
    seed_default_users()

    yield   # application runs here

    # ── SHUTDOWN ──
    logger.info("Saving FAISS index to disk…")
    faiss_store.save()
    logger.info("WorkLens AI shut down cleanly.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="WorkLens AI",
    description="Team work-intelligence platform with RAG-powered insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# NOTE: allow_origins=["*"] cannot be combined with allow_credentials=True per
# the CORS spec (browsers will reject it). Kept as an explicit allow-list from
# the working version instead. Add your deployed frontend origin here too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",    # Streamlit dev
        "http://127.0.0.1:8501",
        "http://localhost:3000",    # if you add a React frontend later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(ai_router)                          # /api/v1/ai/*  (real, not a stub)
app.include_router(auth_router)                         # /api/v1/auth/*

# Uncomment as each router is actually implemented:
# app.include_router(tasks_router,      prefix="/api/v1")
# app.include_router(dashboard_router,  prefix="/api/v1")
# app.include_router(analytics_router,  prefix="/api/v1")
# app.include_router(alerts_router,     prefix="/api/v1")
# app.include_router(feedback_router,   prefix="/api/v1")
# app.include_router(employees_router,  prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "faiss_vectors": faiss_store.total_vectors,
    }


@app.get("/", tags=["Health"])
async def root():
    return {"message": "WorkLens AI is running. Visit /docs for the API."}