from __future__ import annotations

from services.api_client import APIClient, APIClientError


class EmployeeService:
    @staticmethod
    def today_update() -> dict | None:
        try:
            return APIClient.get("/updates/today")
        except Exception:
            # Return None for any failure (API errors, JSON decoding, network issues, etc.)
            # This ensures callers can safely treat exceptions as "no update exists today"
            return None

    @staticmethod
    def tasks(employee_id: int) -> list[dict]:
        try:
            res = APIClient.get(f"/employees/{employee_id}/tasks")
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def feedback(employee_id: int) -> list[dict]:
        try:
            res = APIClient.get(f"/employees/{employee_id}/feedback")
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def risk(employee_id: int) -> dict:
        try:
            res = APIClient.get(f"/employees/{employee_id}/risk")
            return res if isinstance(res, dict) else {"score": 0, "label": "LOW", "factors": []}
        except Exception:
            return {"score": 0, "label": "LOW", "factors": ["No risk data available"]}

    @staticmethod
    def updates(employee_id: int) -> list[dict]:
        try:
            res = APIClient.get(f"/employees/{employee_id}/updates")
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def create_blocker(payload: dict) -> dict:
        return APIClient.post("/blockers", payload)