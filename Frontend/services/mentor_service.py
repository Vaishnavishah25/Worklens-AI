from __future__ import annotations

from services.api_client import APIClient, APIClientError


class MentorService:
    @staticmethod
    def mentees(mentor_id: int):
        return APIClient.get("/employees", params={"mentor_id": mentor_id})

    @staticmethod
    def updates(employee_id: int):
        try:
            return APIClient.get(f"/employees/{employee_id}")
        except APIClientError:
            return []

    @staticmethod
    def risk(employee_id: int):
        try:
            profile = APIClient.get(f"/employees/{employee_id}")
            return {
                "score": profile.get("risk_score", profile.get("score", 0)),
                "label": profile.get("risk", profile.get("label", "Low"))
            }
        except APIClientError:
            return {"score": 0, "label": "Low"}

    @staticmethod
    def feedback(employee_id: int):
        return APIClient.get(f"/feedback/employee/{employee_id}")

    @staticmethod
    def send_feedback(payload: dict):
        return APIClient.post("/feedback", payload)
