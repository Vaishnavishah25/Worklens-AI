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
        print("⚡ Injecting missing 'team_id' column into 'risk_scores' table...")
        # Safe PostgreSQL alteration that appends the column if it's missing
        await conn.execute(text("ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS team_id INTEGER;"))
        
    print("✅ Database columns successfully synchronized with your Python models!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())