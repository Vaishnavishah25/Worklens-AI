# backend/api/v1/dashboard.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from api.deps import role_required
from models.user import User
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
        # Hard isolation: Overwrite parameter to guarantee they only query their assigned mentees
        effective_mentor_id = current_user.id
    else:
        # Administrative access: Managers can see everyone or pass an optional filter ID
        effective_mentor_id = mentor_id

    # pass 'effective_mentor_id' down into your analytics_service.py or repository queries
    # Example: repo.get_team_by_mentor(mentor_id=effective_mentor_id)
    # This ensures that mentors cannot bypass their access level, while managers retain full visibility.

    # Query live database entries using our repository engine
    user_repo = EmployeeRepository(db)
    update_repo = UpdateRepository(db)
    db_employees = await user_repo.get_employees_by_manager(manager_id=effective_mentor_id)
    
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

        serialized_employees.append({
            "id": emp.id,
            "full_name": emp.name,
            "last_update_date": update_date_string,
            "risk": {"score": round((10 - confidence_score) * 0.1, 2),
                     "label": "LOW" if confidence_score > 7 else "MEDIUM" if confidence_score > 4 else "HIGH"},
            "open_blockers": 0
        })
    
    return {
        "access_clearance_level": current_user.role,
        "filtered_by_mentor_scope": effective_mentor_id,
        "team_health_score": 100.0 if not serialized_employees else 85.2,
        "update_completion_rate": 0.0 if not serialized_employees else 0.75,
        "employees": serialized_employees
    }