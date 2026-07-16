from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func

try:
    from app.database.models.daily_update import DailyUpdate
    from app.database.models.blocker import Blocker
except ModuleNotFoundError:
    from database.models.daily_update import DailyUpdate
    from database.models.blocker import Blocker

try:
    from app.database.models.user import User
    from app.database.session import SessionLocal
except ModuleNotFoundError:
    from database.models.user import User
    from database.session import SessionLocal
try:
    from app.database.models.feedback import Feedback
except ModuleNotFoundError:
    from database.models.feedback import Feedback

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Pydantic models ──

class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    title: str | None = None
    manager_id: int | None = None


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    title: str | None = None
    manager_id: int | None = None


class DailyUpdateCreate(BaseModel):
    user_id: int
    work_done: str
    planned_work: str
    confidence_score: float
    blocker_description: str | None = None
    blocker_severity: str | None = None


class DailyUpdateOut(BaseModel):
    id: int
    user_id: int
    work_done: str
    planned_work: str
    confidence_score: float
    created_at: datetime | None = None
    blocker_description: str | None = None
    blocker_severity: str | None = None


class BlockerOut(BaseModel):
    id: int
    user_id: int
    update_id: int
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime | None = None
    employee_name: str | None = None

class FeedbackCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    type: str                 # praise | guidance | concern
    content: str
    visibility: str = "employee_only"


class FeedbackOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    from_name: str | None = None
    to_name: str | None = None
    type: str
    content: str
    visibility: str
    is_read: bool
    created_at: datetime | None = None

class TeamDashboardRow(BaseModel):
    id: int
    name: str
    role: str
    title: str | None = None
    last_update: str | None = None
    open_blockers: int = 0
    avg_confidence: float | None = None
    total_updates: int = 0


# ── Helpers ──

def _hash_password(password: str) -> str:
    secret = os.getenv("JWT_SECRET", "worklens-dev-secret")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), secret.encode("utf-8"), 100_000).hex()


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return _hash_password(plain_password) == hashed_password


def init_db() -> None:
    try:
        from app.database.base import Base
        from app.database.models.user import User  # noqa: F401
        from app.database.models.daily_update import DailyUpdate  # noqa: F401
        from app.database.models.blocker import Blocker  # noqa: F401
        from app.database.models.risk_score import RiskScore  # noqa: F401
        from app.database.models.weekly_summary import WeeklySummary  # noqa: F401
        from app.database.session import engine
        from app.database.models.feedback import Feedback  # noqa: F401
    except ModuleNotFoundError:
        from database.base import Base
        from database.models.user import User  # noqa: F401
        from database.models.daily_update import DailyUpdate  # noqa: F401
        from database.models.blocker import Blocker  # noqa: F401
        from database.models.risk_score import RiskScore  # noqa: F401
        from database.models.weekly_summary import WeeklySummary  # noqa: F401
        from database.session import engine

    required_tables = {"users", "daily_updates", "blockers", "risk_scores", "weekly_summaries","feedback"}
    if engine.url.drivername.startswith("sqlite"):
        db_path = engine.url.database
        if db_path:
            try:
                with sqlite3.connect(db_path, timeout=30) as con:
                    existing_tables = {
                        row[0]
                        for row in con.execute(
                            "select name from sqlite_master where type = 'table'"
                        ).fetchall()
                    }
                if required_tables.issubset(existing_tables):
                    return
            except sqlite3.Error:
                pass

    Base.metadata.create_all(bind=engine)


def seed_default_users() -> None:
    with SessionLocal() as session:
        existing = session.query(User).first()
        if existing is not None:
            return

        manager = User(
            name="Maya Chen",
            email="manager@worklens.ai",
            password=_hash_password("manager123"),
            role="Manager",
            title="Engineering Manager",
        )
        mentor = User(
            name="Ravi Mehta",
            email="mentor@worklens.ai",
            password=_hash_password("mentor123"),
            role="Mentor",
            title="Staff Engineer",
        )
        session.add_all([manager, mentor])
        session.flush()

        employees = [
            User(
                name="Priya Shah",
                email="employee@worklens.ai",
                password=_hash_password("employee123"),
                role="Employee",
                title="Backend Engineer",
                manager_id=manager.id,
            ),
            User(
                name="Anita Rao",
                email="anita@worklens.ai",
                password=_hash_password("employee123"),
                role="Employee",
                title="Frontend Engineer",
                manager_id=manager.id,
            ),
            User(
                name="Jordan Lee",
                email="jordan@worklens.ai",
                password=_hash_password("employee123"),
                role="Employee",
                title="Platform Engineer",
                manager_id=manager.id,
            ),
            User(
                name="Noah Williams",
                email="noah@worklens.ai",
                password=_hash_password("employee123"),
                role="Employee",
                title="Data Engineer",
                manager_id=manager.id,
            ),
            User(
                name="Sara Ahmed",
                email="sara@worklens.ai",
                password=_hash_password("employee123"),
                role="Employee",
                title="QA Engineer",
                manager_id=manager.id,
            ),
        ]
        session.add_all(employees)
        session.commit()


def authenticate_user(email: str, password: str) -> User | None:
    with SessionLocal() as session:
        user = session.query(User).filter(User.email == email.lower()).first()
        if user and _verify_password(password, user.password):
            return user
    return None


# ── Auth endpoints ──

@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest) -> UserOut:
    user = authenticate_user(payload.email.strip().lower(), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        title=getattr(user, "title", None),
        manager_id=user.manager_id,
    )


@router.get("/employees", response_model=list[UserOut])
def list_employees() -> list[UserOut]:
    with SessionLocal() as session:
        users = session.query(User).order_by(User.name).all()
    return [
        UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            title=getattr(user, "title", None),
            manager_id=user.manager_id,
        )
        for user in users
    ]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> UserOut:
    with SessionLocal() as session:
        existing = session.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
        user = User(
            name=payload.name,
            email=payload.email.lower(),
            password=_hash_password(payload.password),
            role=payload.role,
            title=payload.title,
            manager_id=payload.manager_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        title=user.title,
        manager_id=user.manager_id,
    )


# ── Daily update endpoints ──

@router.post("/daily-updates", response_model=DailyUpdateOut, status_code=status.HTTP_201_CREATED)
def create_daily_update(payload: DailyUpdateCreate) -> DailyUpdateOut:
    with SessionLocal() as session:
        update = DailyUpdate(
            user_id=payload.user_id,
            work_done=payload.work_done,
            planned_work=payload.planned_work,
            confidence_score=payload.confidence_score,
        )
        session.add(update)
        session.flush()

        if payload.blocker_description:
            blocker = Blocker(
                user_id=payload.user_id,
                update_id=update.id,
                title="Submitted blocker",
                description=payload.blocker_description,
                severity=payload.blocker_severity or "Medium",
                status="open",
            )
            session.add(blocker)

        session.commit()
        session.refresh(update)

    return DailyUpdateOut(
        id=update.id,
        user_id=update.user_id,
        work_done=update.work_done,
        planned_work=update.planned_work,
        confidence_score=update.confidence_score,
        created_at=update.created_at,
        blocker_description=payload.blocker_description,
        blocker_severity=payload.blocker_severity,
    )


@router.get("/daily-updates", response_model=list[DailyUpdateOut])
def list_daily_updates(user_id: int | None = None) -> list[DailyUpdateOut]:
    """List all daily updates, optionally filtered by user_id."""
    with SessionLocal() as session:
        query = session.query(DailyUpdate).order_by(DailyUpdate.created_at.desc())
        if user_id is not None:
            query = query.filter(DailyUpdate.user_id == user_id)
        updates = query.limit(100).all()

        results = []
        for u in updates:
            blocker_desc = None
            blocker_sev = None
            blocker = session.query(Blocker).filter(Blocker.update_id == u.id).first()
            if blocker:
                blocker_desc = blocker.description
                blocker_sev = blocker.severity
            results.append(DailyUpdateOut(
                id=u.id,
                user_id=u.user_id,
                work_done=u.work_done,
                planned_work=u.planned_work,
                confidence_score=u.confidence_score,
                created_at=u.created_at,
                blocker_description=blocker_desc,
                blocker_severity=blocker_sev,
            ))
    return results


# ── Blocker endpoints ──

@router.get("/blockers", response_model=list[BlockerOut])
def list_blockers(status_filter: str | None = None, user_id: int | None = None) -> list[BlockerOut]:
    with SessionLocal() as session:
        query = session.query(Blocker).order_by(Blocker.created_at.desc())
        if status_filter:
            query = query.filter(Blocker.status == status_filter)
        if user_id is not None:
            query = query.filter(Blocker.user_id == user_id)
        blockers = query.limit(200).all()

        results = []
        for b in blockers:
            user = session.query(User).filter(User.id == b.user_id).first()
            results.append(BlockerOut(
                id=b.id,
                user_id=b.user_id,
                update_id=b.update_id,
                title=b.title,
                description=b.description,
                severity=b.severity,
                status=b.status,
                created_at=b.created_at,
                employee_name=user.name if user else None,
            ))
    return results


# ── Team dashboard summary endpoint ──

@router.get("/team-dashboard", response_model=list[TeamDashboardRow])
def team_dashboard() -> list[TeamDashboardRow]:
    """
    Returns live team dashboard data for the Manager view.
    Includes: per-employee last update time, open blockers count,
    average confidence, and total update count.
    """
    with SessionLocal() as session:
        users = session.query(User).order_by(User.name).all()
        rows = []
        for user in users:
            # last update
            last = (
                session.query(DailyUpdate)
                .filter(DailyUpdate.user_id == user.id)
                .order_by(DailyUpdate.created_at.desc())
                .first()
            )
            last_update_str = last.created_at.isoformat() if last else None

            # open blockers
            open_count = (
                session.query(func.count(Blocker.id))
                .filter(Blocker.user_id == user.id, Blocker.status == "open")
                .scalar()
            ) or 0

            # avg confidence (last 7 updates)
            recent_updates = (
                session.query(DailyUpdate.confidence_score)
                .filter(DailyUpdate.user_id == user.id)
                .order_by(DailyUpdate.created_at.desc())
                .limit(7)
                .all()
            )
            avg_conf = (
                round(sum(r[0] for r in recent_updates) / len(recent_updates), 2)
                if recent_updates
                else None
            )

            # total updates
            total = (
                session.query(func.count(DailyUpdate.id))
                .filter(DailyUpdate.user_id == user.id)
                .scalar()
            ) or 0

            rows.append(TeamDashboardRow(
                id=user.id,
                name=user.name,
                role=user.role,
                title=user.title,
                last_update=last_update_str,
                open_blockers=open_count,
                avg_confidence=avg_conf,
                total_updates=total,
            ))

    return rows

@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate) -> FeedbackOut:
    if payload.type not in ("praise", "guidance", "concern"):
        raise HTTPException(status_code=400, detail="type must be praise/guidance/concern")
    if len(payload.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="content must be at least 10 characters")

    with SessionLocal() as session:
        fb = Feedback(
            from_user_id=payload.from_user_id,
            to_user_id=payload.to_user_id,
            type=payload.type,
            content=payload.content,
            visibility=payload.visibility,
        )
        session.add(fb)
        session.commit()
        session.refresh(fb)
        sender = session.query(User).filter(User.id == fb.from_user_id).first()

    return FeedbackOut(
        id=fb.id, from_user_id=fb.from_user_id, to_user_id=fb.to_user_id,
        from_name=sender.name if sender else None,
        type=fb.type, content=fb.content, visibility=fb.visibility,
        is_read=fb.is_read, created_at=fb.created_at,
    )

class BlockerStatusUpdate(BaseModel):
    status: str  # open | resolved | escalated


@router.put("/blockers/{blocker_id}/status", response_model=BlockerOut)
def update_blocker_status(blocker_id: int, payload: BlockerStatusUpdate) -> BlockerOut:
    if payload.status not in ("open", "resolved", "escalated"):
        raise HTTPException(status_code=400, detail="status must be open/resolved/escalated")
    with SessionLocal() as session:
        b = session.query(Blocker).filter(Blocker.id == blocker_id).first()
        if not b:
            raise HTTPException(status_code=404, detail="Blocker not found")
        b.status = payload.status
        session.commit()
        session.refresh(b)
        user = session.query(User).filter(User.id == b.user_id).first()
    return BlockerOut(
        id=b.id, user_id=b.user_id, update_id=b.update_id, title=b.title,
        description=b.description, severity=b.severity, status=b.status,
        created_at=b.created_at, employee_name=user.name if user else None,
    )

@router.get("/feedback", response_model=list[FeedbackOut])
def list_feedback(user_id: int) -> list[FeedbackOut]:
    """Feedback received BY this user_id, newest first."""
    with SessionLocal() as session:
        rows = (
            session.query(Feedback)
            .filter(Feedback.to_user_id == user_id)
            .order_by(Feedback.created_at.desc())
            .all()
        )
        results = []
        for fb in rows:
            sender = session.query(User).filter(User.id == fb.from_user_id).first()
            results.append(FeedbackOut(
                id=fb.id, from_user_id=fb.from_user_id, to_user_id=fb.to_user_id,
                from_name=sender.name if sender else "Unknown",
                type=fb.type, content=fb.content, visibility=fb.visibility,
                is_read=fb.is_read, created_at=fb.created_at,
            ))
    return results
@router.get("/feedback/team", response_model=list[FeedbackOut])
def list_team_feedback(manager_id: int) -> list[FeedbackOut]:
    """Feedback marked 'employee_manager' for anyone reporting to this manager."""
    with SessionLocal() as session:
        team_ids = [u.id for u in session.query(User).filter(User.manager_id == manager_id).all()]
        if not team_ids:
            return []
        rows = (
            session.query(Feedback)
            .filter(Feedback.to_user_id.in_(team_ids), Feedback.visibility == "employee_manager")
            .order_by(Feedback.created_at.desc())
            .all()
        )
        results = []
        for fb in rows:
            sender = session.query(User).filter(User.id == fb.from_user_id).first()
            recipient = session.query(User).filter(User.id == fb.to_user_id).first()
            results.append(FeedbackOut(
                id=fb.id, from_user_id=fb.from_user_id, to_user_id=fb.to_user_id,
                from_name=sender.name if sender else "Unknown",
                to_name=recipient.name if recipient else "Unknown",
                type=fb.type, content=fb.content, visibility=fb.visibility,
                is_read=fb.is_read, created_at=fb.created_at,
            ))
    return results

@router.put("/feedback/{feedback_id}/ack")
def ack_feedback(feedback_id: int) -> dict:
    with SessionLocal() as session:
        fb = session.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not fb:
            raise HTTPException(status_code=404, detail="Feedback not found")
        fb.is_read = True
        session.commit()
    return {"id": feedback_id, "is_read": True}