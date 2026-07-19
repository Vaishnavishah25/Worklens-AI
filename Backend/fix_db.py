# backend/fix_db.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment configurations
base_dir = Path(__file__).resolve().parent.parent
env_file_path = base_dir / ".env"
if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path)
else:
    load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config import settings

async def main():
    print("🔧 Opening direct structural connection to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        print("Synchronizing database columns with current models...")
        await conn.execute(text("ALTER TABLE daily_updates ADD COLUMN IF NOT EXISTS employee_id INTEGER;"))
        await conn.execute(text("ALTER TABLE daily_updates ADD COLUMN IF NOT EXISTS next_steps TEXT;"))
        await conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'daily_updates' AND column_name = 'user_id'
                ) THEN
                    UPDATE daily_updates SET employee_id = user_id WHERE employee_id IS NULL;
                END IF;
            END $$;
        """))
        await conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'daily_updates' AND column_name = 'planned_work'
                ) THEN
                    UPDATE daily_updates SET next_steps = planned_work WHERE next_steps IS NULL;
                END IF;
            END $$;
        """))
        await conn.execute(text("UPDATE daily_updates SET next_steps = 'Will be updated in next standup' WHERE next_steps IS NULL;"))
        await conn.execute(text("ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS team_id INTEGER;"))
        
    print("✅ Database columns successfully synchronized with your Python models!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
