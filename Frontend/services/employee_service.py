from __future__ import annotations

from services.api_client import APIClient


class EmployeeService:
    @staticmethod
    def today_update():
        return APIClient.get("/updates/today")

    @staticmethod
    def submit_update(payload: dict):
        return APIClient.post("/updates", payload)

    @staticmethod
    def tasks(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/tasks")

    @staticmethod
    def feedback(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/feedback")

    @staticmethod
    def risk(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/risk")

    @staticmethod
    def updates(employee_id: int):
        return APIClient.get(f"/employees/{employee_id}/updates")

    @staticmethod
    def create_blocker(payload: dict):
        return APIClient.post("/blockers", payload)
