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
    def ask_ai(question: str, team_id: str):
        """Query the AI assistant safely using URL parameters."""
        return APIClient.get(
            "/ai/query/sync",
            params={"question": question, "team_id": team_id}
        )
    
    @staticmethod
    def generate_weekly_summary(team_id: str, week_start_date: str):
        """Generate a new AI-powered weekly summary for the team."""
        return APIClient.post(
            "/ai/summarize",
            payload={
                "team_id": team_id,
                "week_start_date": week_start_date
            }
        )

    @staticmethod
    def cached_weekly_summary(team_id: str, week_start_date: str):
        """Retrieve a cached weekly summary for the team using query parameters."""
        return APIClient.get(
            "/ai/summary",
            params={"team_id": team_id, "week_start_date": week_start_date}
        )