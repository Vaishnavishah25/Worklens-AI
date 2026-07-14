# backend/run_tasks.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 🚀 FORCE DIRECTORY ROOT ENVIRONMENT RESOLUTION
base_dir = Path(__file__).resolve().parent.parent
env_file_path = base_dir / ".env"

if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path)
else:
    load_dotenv()

# 🚨 PRE-LOAD THE SQLALCHEMY REGISTRY MAP
# This forces Python to read all relationship models before compiling queries,
# completely preventing the "NameError: name 'Feedback' is not defined" exception.
try:
    from models.user import User
    from models.task import Task
    from models.daily_update import DailyUpdate
    from models.risk_score import RiskScore
    
    # Safely import the feedback model class sheet into memory
    # Note: If your file name is different (e.g., mentor_feedback.py), adjust this import accordingly.
    from models.feedback import Feedback
    
except ImportError as model_err:
    print(f"⚠️ Registry Pre-load Warning: {model_err}")

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings

# Import background operations tasks
from tasks.risk_calc import run_periodic_risk_recalculation
from tasks.alert_scan import scan_and_generate_risk_alerts

# 🔌 INITIALIZE LOCAL ENGINE AND SESSION FACTORY
engine = create_async_engine(settings.DATABASE_URL, echo=False)
LocalSessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False)

async def main():
    print("🚀 Initializing Manual Background Task Verification Pass...")
    async with LocalSessionMaker() as session:
        print("📊 Phase 1: Recalculating all employee risk scores...")
        await run_periodic_risk_recalculation(session)
        
        print("🚨 Phase 2: Scanning metrics for high-risk anomalies...")
        await scan_and_generate_risk_alerts(session)
        
    print("✅ System synchronization successfully committed to database.")

if __name__ == "__main__":
    asyncio.run(main())