# backend/api/v1/dashboard.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_db
from api.deps import role_required
from models.user import User
from models.blocker import Blocker
from models.risk_score import RiskScore
from typing import Optional
from repositories.user_repo import EmployeeRepository
from repositories.daily_update import UpdateRepository

router = APIRouter(prefix="/dashboard", tags=["Leadership Intelligence Monitoring"])


@router.get("/team")
async def get_synchronized_metrics(
    mentor_id: Optional[int] = Query(None), 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Retrieves operational metrics. 
    Managers can view global team elements or filter explicitly by mentor_id.
    Mentors are structurally locked to viewing their own specific mentees.
    """
    # ENFORCE SECURITY TIERS
    if current_user.role == "mentor":
        effective_mentor_id = current_user.id
    else:
        effective_mentor_id = mentor_id

    # Query live database entries using our repository engine
    user_repo = EmployeeRepository(db)
    update_repo = UpdateRepository(db)
    db_employees = await user_repo.get_employees_by_manager(manager_id=effective_mentor_id)
    
    # Get employee IDs for blocker query
    employee_ids = [emp.id for emp in db_employees]
    
    # Query open blockers for all relevant employees
    blockers_result = await db.execute(
        select(Blocker)
        .where(Blocker.user_id.in_(employee_ids))
        .where(Blocker.status == "open")
        .order_by(Blocker.created_at.desc())
    )
    open_blockers = blockers_result.scalars().all()
    
    # Build employee lookup for blocker serialization
    employee_lookup = {emp.id: emp for emp in db_employees}
    
    # Serialize blockers
    serialized_blockers = []
    for blocker in open_blockers:
        emp = employee_lookup.get(blocker.user_id)
        serialized_blockers.append({
            "id": blocker.id,
            "employee": emp.name if emp else "Unknown",
            "blocker": blocker.description,
            "severity": blocker.severity,
            "age": blocker.created_at.isoformat() if blocker.created_at else None,
            "status": blocker.status
        })
    
    # Transform database user models into structural dashboard objects
    serialized_employees = []
    for emp in db_employees:
        latest_update = await update_repo.get_latest_updates(emp.id)
        update_date_string = "No updates logged yet"
        confidence_score = 10

        if latest_update:
            if latest_update.created_at:
                update_date_string = latest_update.created_at.strftime("%Y-%m-%d")
            else:
                update_date_string = "No timestamp available"
            
            confidence_score = latest_update.confidence_score

        # Count open blockers for this employee
        emp_open_blockers = sum(1 for b in open_blockers if b.user_id == emp.id)

        serialized_employees.append({
            "id": emp.id,
            "full_name": emp.name,
            "last_update_date": update_date_string,
            "confidence_score": confidence_score,
            "risk": {
                "score": round((10 - confidence_score) * 0.1, 2),
                "label": "LOW" if confidence_score > 7 else "MEDIUM" if confidence_score > 4 else "HIGH"
            },
            "open_blockers": emp_open_blockers
        })
    
    # Calculate KPIs
    high_risk_count = sum(
        1 for e in serialized_employees
        if e["risk"]["label"] == "HIGH"
    )
    
    open_blockers_count = len(open_blockers)
    
    # Calculate team health score (inverse of risk average, penalized by blockers)
    avg_risk_score = 0
    if serialized_employees:
        avg_risk_score = sum(e["risk"]["score"] for e in serialized_employees) / len(serialized_employees)
    
    team_health_score = max(0, min(100, 100 - (avg_risk_score * 100) - (open_blockers_count * 2)))
    
    # Calculate update completion rate (employees who have submitted updates)
    employees_with_updates = sum(
        1 for e in serialized_employees
        if e["last_update_date"] not in ["No updates logged yet", "No timestamp available"]
    )
    update_completion_rate = (employees_with_updates / len(serialized_employees) * 100) if serialized_employees else 0
    
    # Count unread alerts (high risk + open blockers)
    unread_alerts = high_risk_count + open_blockers_count

    return {
        "kpis": {
            "team_health": round(team_health_score, 2),
            "high_risk": high_risk_count,
            "open_blockers": open_blockers_count,
            "completion_rate": round(update_completion_rate, 2),
            "alerts": unread_alerts
        },
        "employees": [
            {
                "id": e["id"],
                "name": e["full_name"],
                "role": employee_lookup[e["id"]].role if e["id"] in employee_lookup else "employee",
                "confidence": e["confidence_score"],
                "last_update": e["last_update_date"],
                "risk_score": e["risk"]["score"],
                "risk": e["risk"]["label"],
                "risk_trend": "Stable",
                "open_blockers": e["open_blockers"],
                "overdue_tasks": 0,
            }
            for e in serialized_employees
        ],
        "blockers": serialized_blockers
    }