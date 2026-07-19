"""
Backend/app/main.py
WorkLens AI — Unified FastAPI Application
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================================
# Import Routers
# ============================================================================

# Member 1 Routers
from api.v1.auth import router as auth_router
from api.v1.tasks import router as tasks_router
from api.v1.updates import router as updates_router
from api.v1.blockers import router as blockers_router
from api.v1.dashboard import router as dashboard_router
from api.v1.analytics import router as analytics_router
from api.v1.alerts import router as alerts_router
from api.v1.feedback import router as feedback_router
from api.v1.users import router as employees_router

# Member 3 AI Router + Vector Store
from api.v1.ai import router as ai_router
from vectorstore.faiss_store import faiss_store

# Database initialization
from api.v1.auth import init_db, seed_default_users

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)

# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting WorkLens AI...")

    await init_db()
    await seed_default_users()

    logger.info("Database initialized.")
    logger.info("FAISS index loaded (%d vectors)", faiss_store.total_vectors)

    yield

    logger.info("Saving FAISS index...")
    faiss_store.save()
    logger.info("Shutdown complete.")

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="WorkLens AI Platform API",
    version="1.0.0",
    description="Unified backend engine for team analytics, blocker tracking and AI insights.",
    lifespan=lifespan,
)

# ============================================================================
# CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Routers
# ============================================================================

# Core APIs
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(updates_router, prefix="/api/v1")
app.include_router(blockers_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")

# AI APIs
app.include_router(ai_router)

# ============================================================================
# Temporary AI Placeholders
# Remove after full AI integration is merged
# ============================================================================

class AIQuery(BaseModel):
    question: str | None = None
    query: str | None = None


@app.post("/v1/ai/query", tags=["AI Integration Placeholder"])
@app.post("/api/v1/ai/query", tags=["AI Integration Placeholder"])
async def temporary_ai_query(payload: AIQuery):
    return {
        "answer": "WorkLens AI analytical insights are initializing. System base is stable.",
        "citations": [],
        "sources": [],
    }


@app.get("/v1/summaries/weekly", tags=["AI Integration Placeholder"])
@app.get("/api/v1/summaries/weekly", tags=["AI Integration Placeholder"])
async def temporary_weekly_summary():
    return {
        "highlights": [
            "AI automated generation will activate once the vector storage module is merged."
        ],
        "concerns": [],
        "recommendations": [],
    }

# ============================================================================
# Health
# ============================================================================

@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "faiss_vectors": faiss_store.total_vectors,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "WorkLens AI Platform API is running.",
        "docs": "/docs",
    }