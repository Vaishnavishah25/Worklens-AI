from __future__ import annotations

from services.api_client import APIClient


class MentorService:
    @staticmethod
    def mentees(mentor_id: int) -> list[dict]:
        try:
            res = APIClient.get("/employees", params={"mentor_id": mentor_id})
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def updates(employee_id: int) -> list[dict]:
        try:
            res = APIClient.get(f"/employees/{employee_id}/updates")
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def risk(employee_id: int) -> dict:
        try:
            res = APIClient.get(f"/employees/{employee_id}/risk")
            return res if isinstance(res, dict) else {"score": 0, "label": "LOW", "factors": []}
        except Exception:
            return {"score": 0, "label": "LOW", "factors": []}

    @staticmethod
    def feedback(employee_id: int) -> list[dict]:
        try:
            res = APIClient.get(f"/employees/{employee_id}/feedback")
            return res if isinstance(res, list) else []
        except Exception:
            return []

    @staticmethod
    def send_feedback(payload: dict) -> dict:
        return APIClient.post("/feedback", payload)
