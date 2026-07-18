# backend/database/seed.py
import asyncio
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from database.session import AsyncSession, engine 
from database.base import Base
from models.user import User
from auth.password import get_password_hash

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_core_profiles():
    print("Connecting to worklens-postgres and validating schema layout...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test@worklens.ai"))
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            print("Injecting tiered role hierarchy profiles...")
            
            # Generate secure cryptographic password hashes
            manager_pwd = get_password_hash("manager123")
            mentor_pwd = get_password_hash("mentor123")
            employee_pwd = get_password_hash("employee123")

            # Tier 1: Global Platform Administrator (Manager)
            manager = User(
                email="test@worklens.ai",
                hashed_password=manager_pwd,
                role="manager",
                full_name="Maya Chen"
            )
            session.add(manager)

            # Tier 2: Targeted Team Supervisor (Mentor)
            mentor = User(
                email="shruti@worklens.ai",
                hashed_password=mentor_pwd,
                role="mentor",
                full_name="Shruti Panda"
            )
            session.add(mentor)
            
            # Push to database temporarily to generate structural IDs for relationship linking
            await session.flush()

            # Tier 3: Core Team Contributor (Employee bound to their explicit Mentor)
            employee = User(
                email="sai@worklens.ai",
                hashed_password=employee_pwd,
                role="employee",
                full_name="Sai Kumar",
                mentor_id=mentor.id  # Structurally links the mentee to Shruti
            )
            session.add(employee)
            
            await session.commit()
            print("Tiered role initialization successful! Security credentials live.")
        else:
            print("System records are already populated. Skipping execution cycle.")

if __name__ == "__main__":
    asyncio.run(seed_core_profiles())