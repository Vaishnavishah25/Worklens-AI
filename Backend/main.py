# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.v1 import tasks, blockers, updates, auth, dashboard, users
from api.v1.auth import router as auth_router

from database.session import engine, get_db
from database.base import Base
import models

from schemas.daily_update import UpdateCreate
from services.update_service import UpdateService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on application startup
    async with engine.begin() as conn:
        # 1. Auto-create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. ⛑️ Seed default user with columns matching Member 1's exact model names ('name')
        await conn.execute(text("""
            INSERT INTO users (id, name, email, password, role)
            VALUES (1, 'Default User', 'test@worklens.ai', 'no_pass', 'employee')
            ON CONFLICT (id) DO NOTHING;
        """))
    yield

app = FastAPI(title="WorkLens AI Operational API", version="1.0-MVP", description="Operational tracking system endpoints", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ADDED HERE: Mount your separate feature routers under the /v1 namespace
app.include_router(updates.router, prefix="/v1")
app.include_router(tasks.router, prefix="/v1")
app.include_router(blockers.router, prefix="/v1")
app.include_router(dashboard.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")

# Raw root endpoints

@app.post("/v1/updates", status_code=201)
async def submit_standup(payload: UpdateCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = UpdateService(db)
        db_update, risk_label = await service.process_and_save(payload, user_id=1)
        return {
            "id": db_update.id,
            "status": "success",
            "risk_assigned": risk_label
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/ai/query")
async def ask_worklens_assistant(payload: dict):
    return {
        "response": f"AI Engine Active. Ready for Member 3's RAG module to analyze: '{payload.get('question')}'"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}