# backend/repositories/user_repo.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user import User

class EmployeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def create_user(self, user_obj: User) -> User:
        self.db.add(user_obj)
        await self.db.commit()
        await self.db.refresh(user_obj)
        return user_obj
    
    # NEW: Dynamic lookup for a supervisor's team roster
    async def get_employees_by_manager(self, manager_id: Optional[int]) -> List[User]:
        query = select(User)
        if manager_id is not None:
            query = query.where(User.manager_id == manager_id)
        else:
            # If manager views globally, fetch all team contributors
            query = query.where(User.role == "employee")
            
        result = await self.db.execute(query)
        return list(result.scalars().all())