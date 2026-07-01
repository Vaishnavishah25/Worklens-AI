from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database.base import Base
from models.blocker import Blocker
from models.daily_update import DailyUpdate
from models.risk_score import RiskScore
from models.user import User
from database.session import engine, get_db


API_PREFIX = "/api/v1"
JWT_SECRET = "worklens-local-dev-secret"


USERS = {
    "manager@worklens.ai": {
        "id": 1,
        "name": "Maya Chen",
        "email": "manager@worklens.ai",
        "password": "manager123",
        "role": "manager",
        "designation": "Engineering Manager",
        "manager_id": None,
    },
    "mentor@worklens.ai": {
        "id": 2,
        "name": "Ravi Mehta",
        "email": "mentor@worklens.ai",
        "password": "mentor123",
        "role": "mentor",
        "designation": "Senior Mentor",
        "manager_id": 1,
    },
    "employee@worklens.ai": {
        "id": 3,
        "name": "Priya Shah",
        "email": "employee@worklens.ai",
        "password": "employee123",
        "role": "employee",
        "designation": "Software Engineer",
        "manager_id": 2,
    },
    "anita@worklens.ai": {
        "id": 4,
        "name": "Anita Rao",
        "email": "anita@worklens.ai",
        "password": "employee123",
        "role": "employee",
        "designation": "Frontend Engineer",
        "manager_id": 2,
    },
    "jordan@worklens.ai": {
        "id": 5,
        "name": "Jordan Lee",
        "email": "jordan@worklens.ai",
        "password": "employee123",
        "role": "employee",
        "designation": "Platform Engineer",
        "manager_id": 2,
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateCreate(BaseModel):
    employee_name: str | None = None
    work_done: str
    blockers: str | None = None
    severity: str = "None"
    next_steps: str | None = None
    confidence: int


class BlockerCreate(BaseModel):
    employee_id: int
    description: str
    severity: str = "Medium"


class FeedbackCreate(BaseModel):
    employee_id: int
    type: str
    message: str
    visibility: str = "Employee and manager"


class AIQuery(BaseModel):
    question: str | None = None
    query: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for user in USERS.values():
            await conn.execute(
                text(
                    """
                    INSERT INTO users (id, name, email, password, role, manager_id)
                    VALUES (:id, :name, :email, :password, :role, :manager_id)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        password = EXCLUDED.password,
                        role = EXCLUDED.role,
                        manager_id = EXCLUDED.manager_id
                    """
                ),
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "password": user["password"],
                    "role": user["role"],
                    "manager_id": user["manager_id"],
                },
            )
    yield


app = FastAPI(title="WorkLens AI Operational API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(message: str) -> str:
    digest = hmac.new(JWT_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    return _b64(digest)


def _token(user: dict[str, Any], ttl_seconds: int) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(
        json.dumps(
            {
                "sub": user["id"],
                "role": user["role"],
                "name": user["name"],
                "exp": int(time.time()) + ttl_seconds,
            }
        ).encode()
    )
    signature = _sign(f"{header}.{payload}")
    return f"{header}.{payload}.{signature}"


def _decode_token(token: str) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(f"{header}.{payload}")):
            raise ValueError("bad signature")
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if int(data["exp"]) < int(time.time()):
            raise ValueError("expired")
        return data
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return _decode_token(authorization.removeprefix("Bearer ").strip())


def require_roles(*roles: str):
    def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return dependency


def _designation(user: User) -> str:
    return next(
        (item["designation"] for item in USERS.values() if item["email"] == user.email),
        user.role.title(),
    )


async def _employee(db: AsyncSession, employee_id: int) -> User:
    employee = await db.get(User, employee_id)
    if not employee or employee.role != "employee":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    return employee


async def _latest_update(db: AsyncSession, employee_id: int) -> DailyUpdate | None:
    result = await db.execute(
        select(DailyUpdate)
        .where(DailyUpdate.user_id == employee_id)
        .order_by(DailyUpdate.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _latest_risk(db: AsyncSession, employee_id: int) -> tuple[float, str]:
    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.employee_id == employee_id)
        .order_by(RiskScore.created_at.desc())
        .limit(1)
    )
    risk = result.scalar_one_or_none()
    if risk:
        return risk.score, risk.label.title()

    open_blockers = await _open_blocker_count(db, employee_id)
    latest_update = await _latest_update(db, employee_id)
    confidence = latest_update.confidence_score if latest_update else 3
    score = min(100, int(open_blockers * 25 + max(0, 5 - confidence) * 12))
    label = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
    return score, label


async def _open_blocker_count(db: AsyncSession, employee_id: int) -> int:
    result = await db.execute(
        select(Blocker).where(Blocker.user_id == employee_id, Blocker.status != "resolved")
    )
    return len(result.scalars().all())


async def _employee_row(db: AsyncSession, employee: User) -> dict[str, Any]:
    latest = await _latest_update(db, employee.id)
    risk_score, risk = await _latest_risk(db, employee.id)
    open_blockers = await _open_blocker_count(db, employee.id)
    mentor = await db.get(User, employee.manager_id) if employee.manager_id else None
    return {
        "id": employee.id,
        "name": employee.name,
        "role": _designation(employee),
        "mentor_id": employee.manager_id,
        "mentor": mentor.name if mentor else "",
        "last_update": latest.created_at.strftime("%b %d, %I:%M %p") if latest else "Missing",
        "risk_score": risk_score,
        "risk": risk,
        "risk_trend": "Stable",
        "open_blockers": open_blockers,
        "overdue_tasks": 0,
        "confidence": latest.confidence_score if latest else 0,
    }


async def _employee_rows(db: AsyncSession, mentor_id: int | None = None) -> list[dict[str, Any]]:
    query = select(User).where(User.role == "employee")
    if mentor_id is not None:
        query = query.where(User.manager_id == mentor_id)
    result = await db.execute(query.order_by(User.name))
    return [await _employee_row(db, employee) for employee in result.scalars().all()]


async def _blocker_rows(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(select(Blocker).order_by(Blocker.id.desc()))
    rows = result.scalars().all()
    employees_by_id = {row["id"]: row for row in await _employee_rows(db)}
    return [
        {
            "id": row.id,
            "employee_id": row.user_id,
            "employee": employees_by_id.get(row.user_id, {}).get("name", "Employee"),
            "blocker": row.description,
            "severity": row.severity.title(),
            "age": "0d",
            "status": row.status.title(),
        }
        for row in rows
    ]


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post(f"{API_PREFIX}/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.username.strip().lower()))
    user = result.scalar_one_or_none()
    if not user or user.password != payload.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    token_user = {"id": user.id, "role": user.role, "name": user.name}
    public_user = {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "designation": _designation(user),
        "email": user.email,
    }
    return {
        "access_token": _token(token_user, 3600),
        "refresh_token": _token(token_user, 86400),
        "user": public_user,
    }


@app.get(f"{API_PREFIX}/updates/today")
async def today_update(db: AsyncSession = Depends(get_db), user=Depends(require_roles("employee"))):
    result = await db.execute(
        select(DailyUpdate)
        .where(DailyUpdate.user_id == user["sub"])
        .order_by(DailyUpdate.created_at.desc())
        .limit(1)
    )
    update = result.scalar_one_or_none()
    if not update:
        return None
    return {
        "id": update.id,
        "work_done": update.work_done,
        "next_steps": update.planned_work,
        "confidence": update.confidence_score,
        "created_at": update.created_at.isoformat(),
    }


@app.post(f"{API_PREFIX}/updates", status_code=201)
async def submit_update(payload: UpdateCreate, db: AsyncSession = Depends(get_db), user=Depends(require_roles("employee"))):
    blocker_count = 1 if payload.blockers and payload.blockers.strip() else 0
    risk_score = min(100, int(blocker_count * 35 + max(0, 5 - payload.confidence) * 15))
    risk_label = "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"
    update = DailyUpdate(
        user_id=user["sub"],
        work_done=payload.work_done,
        planned_work=payload.next_steps or "Not provided",
        confidence_score=float(payload.confidence),
    )
    db.add(update)
    await db.flush()
    if payload.blockers and payload.blockers.strip():
        db.add(
            Blocker(
                user_id=user["sub"],
                update_id=update.id,
                title="Daily update blocker",
                description=payload.blockers,
                severity=payload.severity if payload.severity != "None" else "Medium",
                status="open",
            )
        )
    db.add(RiskScore(employee_id=user["sub"], score=float(risk_score), label=risk_label))
    await db.commit()
    await db.refresh(update)
    return {"id": update.id, "status": "success", "risk_assigned": risk_label}


@app.get(f"{API_PREFIX}/employees")
async def employees(mentor_id: int | None = None, db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager", "mentor"))):
    return await _employee_rows(db, mentor_id)


@app.get(f"{API_PREFIX}/employees/{{employee_id}}/tasks")
async def employee_tasks(employee_id: int, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    await _employee(db, employee_id)
    return []


@app.get(f"{API_PREFIX}/employees/{{employee_id}}/feedback")
async def employee_feedback(employee_id: int, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    await _employee(db, employee_id)
    return []


@app.get(f"{API_PREFIX}/employees/{{employee_id}}/risk")
async def employee_risk(employee_id: int, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    await _employee(db, employee_id)
    score, label = await _latest_risk(db, employee_id)
    return {
        "score": score,
        "label": label,
        "factors": ["Open blockers", "Confidence trend", "Overdue tasks"],
    }


@app.get(f"{API_PREFIX}/employees/{{employee_id}}/updates")
async def employee_updates(employee_id: int, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    await _employee(db, employee_id)
    result = await db.execute(select(DailyUpdate).where(DailyUpdate.user_id == employee_id).order_by(DailyUpdate.created_at.desc()))
    return [
        {
            "id": row.id,
            "work_done": row.work_done,
            "next_steps": row.planned_work,
            "confidence": row.confidence_score,
            "created_at": row.created_at.isoformat(),
        }
        for row in result.scalars().all()
    ]


@app.post(f"{API_PREFIX}/blockers", status_code=201)
async def create_blocker(payload: BlockerCreate, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    await _employee(db, payload.employee_id)
    update = DailyUpdate(user_id=payload.employee_id, work_done="Blocker reported", planned_work="Resolve blocker", confidence_score=3)
    db.add(update)
    await db.flush()
    blocker = Blocker(
        user_id=payload.employee_id,
        update_id=update.id,
        title="Reported blocker",
        description=payload.description,
        severity=payload.severity,
        status="open",
    )
    db.add(blocker)
    await db.commit()
    await db.refresh(blocker)
    return {"id": blocker.id, "status": blocker.status}


@app.put(f"{API_PREFIX}/blockers/{{blocker_id}}/resolve")
async def resolve_blocker(blocker_id: int, db: AsyncSession = Depends(get_db), user=Depends(current_user)):
    blocker = await db.get(Blocker, blocker_id)
    if not blocker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Blocker not found")
    blocker.status = "resolved"
    await db.commit()
    return {"id": blocker.id, "status": blocker.status}


@app.get(f"{API_PREFIX}/dashboard/team")
async def dashboard_team(db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager"))):
    blockers = await _blocker_rows(db)
    employees = await _employee_rows(db)
    high_risk = len([row for row in employees if row["risk"] == "High"])
    submitted = len([row for row in employees if row["last_update"] != "Missing"])
    completion = int((submitted / len(employees)) * 100) if employees else 0
    return {
        "kpis": {
            "team_health": 78,
            "high_risk": high_risk,
            "open_blockers": len([b for b in blockers if b["status"] != "Resolved"]),
            "completion_rate": completion,
            "alerts": high_risk + len([b for b in blockers if b["status"] != "Resolved"]),
        },
        "employees": employees,
        "blockers": blockers,
    }


@app.get(f"{API_PREFIX}/alerts")
async def alerts(db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager"))):
    employees = await _employee_rows(db)
    blockers = await _blocker_rows(db)
    alerts_list = [
        {"level": "Critical", "message": f"{row['name']} is high risk."}
        for row in employees
        if row["risk"] == "High"
    ]
    alerts_list.extend(
        {"level": "Warning", "message": f"{row['employee']} has an open blocker: {row['blocker']}"}
        for row in blockers
        if row["status"] != "Resolved"
    )
    return alerts_list or [{"level": "Info", "message": "No active team alerts."}]


@app.get(f"{API_PREFIX}/analytics/team")
async def analytics_team(db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager"))):
    employees = await _employee_rows(db)
    dist = {"Low": 0, "Medium": 0, "High": 0}
    for row in employees:
        dist[row["risk"]] = dist.get(row["risk"], 0) + 1
    avg_conf = sum(row["confidence"] for row in employees) / len(employees) if employees else 0
    return {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "health": [round(avg_conf * 20)] * 5,
        "risk_distribution": dist,
    }


@app.get(f"{API_PREFIX}/analytics/blockers")
async def analytics_blockers(db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager"))):
    blockers = await _blocker_rows(db)
    return {"labels": ["W1", "W2", "W3", "W4"], "counts": [2, 4, 3, len(blockers)]}


@app.post(f"{API_PREFIX}/ai/query")
async def ai_query(payload: AIQuery, user=Depends(require_roles("manager"))):
    question = payload.query or payload.question or "team risk"
    return {
        "answer": f"Based on current WorkLens signals, focus first on high-risk employees and aging blockers related to: {question}",
        "citations": [
            {"title": "Team Risk Overview", "source": "/api/v1/dashboard/team"},
            {"title": "Blocker Analytics", "source": "/api/v1/analytics/blockers"},
        ],
        "sources": ["risk_scores", "daily_updates", "blockers"],
    }


@app.get(f"{API_PREFIX}/summaries/weekly")
async def weekly_summary(db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager"))):
    employees = await _employee_rows(db)
    blockers = await _blocker_rows(db)
    high_risk = [row["name"] for row in employees if row["risk"] == "High"]
    missing = [row["name"] for row in employees if row["last_update"] == "Missing"]
    return {
        "highlights": [f"{len(employees) - len(missing)} of {len(employees)} employees have submitted updates."],
        "concerns": [f"{name} is currently high risk." for name in high_risk] or ["No high-risk employees detected."],
        "recommendations": [f"Review {len(blockers)} open blockers and follow up on missing updates."],
    }


@app.post(f"{API_PREFIX}/feedback", status_code=201)
async def create_feedback(payload: FeedbackCreate, db: AsyncSession = Depends(get_db), user=Depends(require_roles("manager", "mentor"))):
    await _employee(db, payload.employee_id)
    return {
        "status": "accepted",
        "message": "Feedback endpoint received the request. Add a feedback table to persist history.",
    }


@app.post("/v1/updates", status_code=201)
async def legacy_submit_update(payload: UpdateCreate, db: AsyncSession = Depends(get_db), user=Depends(require_roles("employee"))):
    return await submit_update(payload, db, user)


@app.post("/v1/ai/query")
async def legacy_ai_query(payload: AIQuery, user=Depends(require_roles("manager"))):
    return await ai_query(payload, user)
