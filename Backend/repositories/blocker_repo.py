# app/repositories/blocker_repo.py
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models.blocker import Blocker
from models.user import User

class BlockerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_standalone(
        self,
        user_id: int,
        title: str,
        description: str,
        severity: str
    ) -> Blocker:
        db_blocker = Blocker(
            user_id=user_id,
            update_id=None,
            title=title,
            description=description,
            severity=severity,
            status="open"
        )
        self.db.add(db_blocker)
        await self.db.commit()
        await self.db.refresh(db_blocker)
        return db_blocker

    async def resolve(self, blocker_id: int) -> Optional[Blocker]:
        result = await self.db.execute(select(Blocker).where(Blocker.id == blocker_id))
        db_blocker = result.scalar_one_or_none()
        if db_blocker:
            db_blocker.status = "resolved"
            await self.db.commit()
            await self.db.refresh(db_blocker)
        return db_blocker
    
    async def get_open_by_user(self, user_id: int) -> List[Blocker]:
        result = await self.db.execute(
            select(Blocker)
            .where(
                Blocker.user_id == user_id,
                func.lower(Blocker.status) == "open"
            )
            .order_by(Blocker.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_open_by_team(self, team_id: int) -> List[Blocker]:
        result = await self.db.execute(
            select(Blocker)
            .join(User, User.id == Blocker.user_id)
            .where(
                User.team_id == team_id,
                func.lower(Blocker.status) == "open"
            )
            .order_by(Blocker.created_at.desc())
        )
        return list(result.scalars().all())