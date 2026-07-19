from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from api.deps import role_required
from models.user import User

router = APIRouter(
    prefix="/summaries",
    tags=["AI Weekly Summaries"]
)


@router.get("/weekly")
async def get_weekly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["manager", "mentor"]))
):
    """
    Temporary weekly summary endpoint.
    Returns the structure expected by the frontend.
    """

    return {
        "highlights": [
            "Team update completion is healthy.",
            "No critical blockers were reported this week.",
            "Overall team productivity remains stable."
        ],
        "concerns": [
            "Some employees have not submitted recent updates.",
            "Monitor medium-risk members closely."
        ],
        "recommendations": [
            "Schedule 1:1 meetings with high-risk employees.",
            "Encourage daily update submissions.",
            "Review blocker trends during the next stand-up."
        ]
    }