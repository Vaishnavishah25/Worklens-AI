from __future__ import annotations

from services.api_client import APIClient, APIClientError


class EmployeeService:
    @staticmethod
    def today_update():
        try:
            return APIClient.get("/updates/today")
        except APIClientError:
            return {}

    @staticmethod
    def submit_update(payload: dict):
        return APIClient.post("/updates/updates", payload)

    @staticmethod
    def tasks(employee_id: int):
        return APIClient.get("/tasks")

    @staticmethod
    def feedback(employee_id: int):
        return APIClient.get(f"/feedback/employee/{employee_id}")

    @staticmethod
    def risk(employee_id: int):
        try:
            profile = APIClient.get(f"/employees/{employee_id}")
            return {
                "score": profile.get("risk_score", profile.get("score", 0)),
                "label": profile.get("risk", profile.get("label", "Low")),
                "factors": profile.get("factors", ["No risk factors detected"])
            }
        except APIClientError:
            return {"score": 0, "label": "Low", "factors": ["No risk metrics found"]}
        
    @staticmethod
    def updates(employee_id: int):
        try:
            profile = APIClient.get(f"/employees/{employee_id}")
            if isinstance(profile, list):
                return profile
            if isinstance(profile, dict):
                return profile.get("updates", [])
            return []
        except APIClientError:
            return []

    @staticmethod
    def create_blocker(payload: dict):
        return APIClient.post("/blockers", payload)
