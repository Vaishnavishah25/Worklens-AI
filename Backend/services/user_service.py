# backend/services/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from typing import Optional

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Looks up a user profile by their email address.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Looks up a user profile by their primary key integer ID.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()