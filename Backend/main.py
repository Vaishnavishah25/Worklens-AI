from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 🔌 Import your verified modular feature routers
from api.v1.auth import router as auth_router
from api.v1.tasks import router as tasks_router
from api.v1.updates import router as updates_router
from api.v1.blockers import router as blockers_router
from api.v1.dashboard import router as dashboard_router
from api.v1.analytics import router as analytics_router
from api.v1.alerts import router as alerts_router
from api.v1.feedback import router as feedback_router
from api.v1.users import router as employees_router

app = FastAPI(
    title="WorkLens AI Platform API",
    version="1.0.0",
    description="Unified core backend engine for team anomaly tracking and risk analytics."
)

# CORS Configuration to allow Member 1's frontend to communicate smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(updates_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(blockers_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")


# Temporary Integration Placeholders for AI/Summary Features
# (These dual decorators keep the frontend UI fully functional until Member 3's AI branch is merged)
class AIQuery(BaseModel):
    question: str | None = None
    query: str | None = None

@app.post("/v1/ai/query", tags=["AI Integration Placeholder"])
@app.post("/api/v1/ai/query", tags=["AI Integration Placeholder"])
async def temporary_ai_query(payload: AIQuery):
    return {
        "answer": "WorkLens AI analytical insights are initializing. System base is stable.",
        "citations": [],
        "sources": []
    }

@app.get("/v1/summaries/weekly", tags=["AI Integration Placeholder"])
@app.get("/api/v1/summaries/weekly", tags=["AI Integration Placeholder"])
async def temporary_weekly_summary():
    return {
        "highlights": ["AI automated generation will activate once the vector storage module is pulled down."],
        "concerns": [],
        "recommendations": []
    }


# Core System Verification Endpoints
@app.get("/health", tags=["System Health"])
async def health_check():
    return {"status": "healthy"}