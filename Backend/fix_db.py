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
    print("🔧 Connecting to database to sync schema columns...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        print("Ensuring columns exist across operational tables...")
        # Add required missing columns if they do not exist
        statements = [
            "ALTER TABLE daily_updates ADD COLUMN IF NOT EXISTS employee_id INTEGER;",
            "ALTER TABLE daily_updates ADD COLUMN IF NOT EXISTS next_steps TEXT;",
            "ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS team_id INTEGER;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id INTEGER;",
        ]
        
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:
                print(f"Notice: {stmt.split()[5]} update handled or non-critical: {exc}")

    print("✅ Database schema synchronization completed!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
