# backend/run_tasks.py

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent
env_file_path = base_dir / ".env"
if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path)
else:
    load_dotenv()

# Force load models into SQLAlchemy registry
from models import User, Task, DailyUpdate, RiskScore, Blocker, Feedback

from database.session import SessionLocal
from tasks.risk_calc import run_periodic_risk_recalculation
from tasks.alert_scan import scan_and_generate_risk_alerts


async def main():
    print("🚀 Initializing Background Verification Pass...")
    async with SessionLocal() as session:
        print("📊 Phase 1: Recalculating employee risk scores...")
        await run_periodic_risk_recalculation(session)
        
        print("🚨 Phase 2: Scanning for high-risk alerts...")
        await scan_and_generate_risk_alerts(session)
        
    print("✅ System synchronization successfully completed.")


if __name__ == "__main__":
    asyncio.run(main())