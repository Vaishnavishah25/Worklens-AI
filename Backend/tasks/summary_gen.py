# backend/tasks/summary_gen.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.task import Task
from models.blocker import Blocker
from typing import Dict, Any

async def generate_weekly_performance_summary(db: AsyncSession, employee_id: int) -> Dict[str, Any]:
    """
    Compiles relational table records into structured performance summaries 
    for review by team leads.
    """
    # Gather completed work units
    task_res = await db.execute(select(Task).where(Task.employee_id == employee_id, Task.status == "done"))
    done_tasks = task_res.scalars().all()

    # Gather remaining obstacles
    blocker_res = await db.execute(select(Blocker).where(Blocker.user_id == employee_id, Blocker.status == "open"))
    open_blockers = blocker_res.scalars().all()

    summary_text = f"Completed {len(done_tasks)} operational development objectives this cycle. "
    if open_blockers:
        summary_text += f"Currently dealing with {len(open_blockers)} open deployment blockers."
    else:
        summary_text += "No major architecture obstacles listed."

    return {
        "employee_id": employee_id,
        "summary_narrative": summary_text,
        "metrics_snapshot": {
            "tasks_resolved": len(done_tasks),
            "blockers_remaining": len(open_blockers)
        }
    }