from __future__ import annotations

from services.api_client import APIClient


class ManagerService:
    @staticmethod
    def dashboard():
        return APIClient.get("/dashboard/team")

    @staticmethod
    def alerts():
        return APIClient.get("/alerts")

    @staticmethod
    def team_analytics():
        return APIClient.get("/analytics/team")

    @staticmethod
    def blocker_analytics():
        return APIClient.get("/analytics/blockers")

    @staticmethod
    def weekly_summary():
        return APIClient.get("/summaries/weekly")

    @staticmethod
    def ask_ai(question: str):
        return APIClient.post("/ai/query",
        {
            "question": question,
            "team_id": "00000000-0000-0000-0000-000000000001"
        },
    )