from __future__ import annotations

from services.api_client import APIClient


class MentorService:
    @staticmethod
    def mentees(mentor_id: int):
        return APIClient.get("/employees", params={"mentor_id": mentor_id})

    @staticmethod
    def updates(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/updates")

    @staticmethod
    def risk(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/risk")

    @staticmethod
    def feedback(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/feedback")

    @staticmethod
    def send_feedback(payload: dict):
        return APIClient.post("/feedback", payload)
