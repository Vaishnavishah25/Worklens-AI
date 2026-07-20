from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from schemas.blocker import BlockerCreate, BlockerResponse
from repositories.blocker_repo import BlockerRepository
from api.deps import role_required
from models.user import User

router = APIRouter(prefix="/blockers", tags=["Operational Blockers"])

@router.post("", response_model=BlockerResponse, status_code=201)
async def report_mid_day_blocker(
    payload: BlockerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["employee", "manager", "mentor"]))
):
    repo = BlockerRepository(db)
    db_blocker = await repo.create_standalone(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity
    )
    
    # Bridge notice for Member 3's background vectorization triggers
    print(f"Baking vector hook for blocker context id: {db_blocker.id}")
    return db_blocker

@router.put("/{blocker_id}/resolve", response_model=BlockerResponse)
async def clear_active_blocker(
    blocker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(["employee", "manager", "mentor"]))
):
    repo = BlockerRepository(db)
    updated = await repo.resolve(blocker_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Blocker signature not found")
    return updated
