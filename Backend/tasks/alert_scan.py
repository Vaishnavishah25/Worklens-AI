# backend/tasks/alert_scan.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.risk_score import RiskScore
from services.alert_service import Alert
from datetime import datetime, timezone

async def scan_and_generate_risk_alerts(db: AsyncSession):
    """
    Scans recent risk records and logs high-priority system alerts 
    for users needing intervention.
    """
    # 1. Fetch all rows currently operating at high risk levels
    query = select(RiskScore).where(RiskScore.label == "HIGH")
    result = await db.execute(query)
    high_risk_records = result.scalars().all()

    for record in high_risk_records:
        # 2. Check if an unacknowledged alert already exists to prevent duplicate spam
        alert_query = select(Alert).where(
            Alert.employee_id == record.employee_id,
            Alert.type == "high_risk_anomaly",
            Alert.is_acknowledged == False
        )
        alert_res = await db.execute(alert_query)
        existing_alert = alert_res.scalar_one_or_none()

        if not existing_alert:
            # Dynamically fetch the employee's name for contextual clarity
            from models.user import User
            user_res = await db.execute(select(User).where(User.id == record.employee_id))
            user_obj = user_res.scalar_one_or_none()
            emp_name = user_obj.name if user_obj else f"User ID {record.employee_id}"

            # Append the high priority flag directly into the operations engine
            new_alert = Alert(
                employee_id=record.employee_id,
                team_id=record.team_id,
                type="high_risk_anomaly",
                message=f"Critical Alert: {emp_name}'s overall health index has crossed into the HIGH tier. Immediate intervention advised.",
                is_acknowledged=False
            )
            db.add(new_alert)

    await db.commit()