"""
Backend/app/main.py
WorkLens AI — FastAPI application entry point.
"""

from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()                          # must be first — loads .env before anything else



# ── Member 3 router ──────────────────────────────────────────────────────────
try:
    from api.v1.ai import router as ai_router
    from api.v1.auth import router as auth_router
    from vectorstore.faiss_store import faiss_store
except ModuleNotFoundError:
    from api.v1.ai import router as ai_router
    from api.v1.auth import router as auth_router
    from vectorstore.faiss_store import faiss_store

# ── Member 1 routers (uncomment as they build them) ──────────────────────────
# from api.v1.employees  import router as employees_router
# from api.v1.updates    import router as updates_router
# from api.v1.blockers   import router as blockers_router
# from api.v1.tasks      import router as tasks_router
# from api.v1.dashboard  import router as dashboard_router
# from api.v1.analytics  import router as analytics_router
# from api.v1.alerts     import router as alerts_router
# from api.v1.feedback   import router as feedback_router

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

# ── CORS — allow Streamlit frontend on port 8501 ─────────────────────────────

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

app.include_router(ai_router)           # Member 3 — /api/v1/ai/*

# Uncomment these one by one as Member 1 finishes each file:
app.include_router(auth_router)
# app.include_router(employees_router)
# app.include_router(updates_router)
# app.include_router(blockers_router)
# app.include_router(tasks_router)
# app.include_router(dashboard_router)
# app.include_router(analytics_router)
# app.include_router(alerts_router)
# app.include_router(feedback_router)


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