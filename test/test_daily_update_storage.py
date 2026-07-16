import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "Backend" / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from database.models.daily_update import DailyUpdate
from database.session import SessionLocal
from main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_daily_update_is_persisted_to_database(client):
    response = client.post(
        "/api/v1/auth/daily-updates",
        json={
            "user_id": 1,
            "work_done": "Implemented the new daily update endpoint",
            "planned_work": "Verify the UI submits the payload",
            "confidence_score": 4.2,
            "blocker_description": "Waiting for final review",
            "blocker_severity": "Medium",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["work_done"] == "Implemented the new daily update endpoint"

    with SessionLocal() as session:
        saved = session.get(DailyUpdate, body["id"])
        assert saved is not None
        assert saved.work_done == "Implemented the new daily update endpoint"
        assert saved.planned_work == "Verify the UI submits the payload"
