# backend/repositories/feedback_repo.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.feedback import Feedback

class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        mentor_id: int,
        mentee_id: int,
        feedback_type: str,
        visibility: str,
        message: str
    ) -> Feedback:
        db_feedback = Feedback(
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            type=feedback_type,
            visibility=visibility,
            message=message
        )
        self.db.add(db_feedback)
        await self.db.commit()
        await self.db.refresh(db_feedback)
        return db_feedback

    async def get_by_id(self, feedback_id: int) -> Optional[Feedback]:
        result = await self.db.execute(select(Feedback).where(Feedback.id == feedback_id))
        return result.scalar_one_or_none()

    async def get_feedback_by_mentor(self, mentor_id: int) -> List[Feedback]:
        result = await self.db.execute(
            select(Feedback)
            .where(Feedback.mentor_id == mentor_id)
            .order_by(Feedback.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_feedback_for_employee(self, employee_id: int) -> List[Feedback]:
        result = await self.db.execute(
            select(Feedback)
            .where(Feedback.mentee_id == employee_id)
            .order_by(Feedback.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, feedback_id: int) -> Optional[Feedback]:
        feedback = await self.get_by_id(feedback_id)
        if feedback:
            await self.db.delete(feedback)
            await self.db.commit()
        return feedback