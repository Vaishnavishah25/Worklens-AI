from __future__ import annotations

from services.api_client import APIClient, APIClientError
from utils.session import SessionManager


class AuthService:
    @classmethod
    def login(cls, email: str, password: str) -> tuple[bool, str]:
        try:
            payload = APIClient.post(
                "/auth/login",
                {"email": email.strip().lower(), "password": password},
                include_auth=False,
            )
        except APIClientError as exc:
            return False, exc.user_message

        # 🛡️ Defensive Extraction: Fall back to root payload if "user" key is missing
        user = payload.get("user", payload)
        
        SessionManager.login(
            user=user,
            access_token=payload.get("access_token"),
            refresh_token=payload.get("refresh_token"),
        )
        return True, "Login successful."

    @classmethod
    def signup(
        cls,
        name: str,
        email: str,
        password: str,
        role: str,
        manager_id: int | None = None,
    ) -> tuple[bool, str]:
        payload = {
            "name": name.strip(),
            "email": email.strip().lower(),
            "password": password,
            "role": role.strip().lower(),
            "manager_id": manager_id,
        }
        try:
            response = APIClient.post("/auth/signup", payload, include_auth=False)
        except APIClientError as exc:
            return False, exc.user_message

        # 🛡️ Defensive Extraction: Fall back to root response if "user" key is missing
        user = response.get("user", response)
        
        SessionManager.login(
            user=user,
            access_token=response.get("access_token"),
            refresh_token=response.get("refresh_token"),
        )
        return True, "Account created successfully."

    @classmethod
    def logout(cls):
        SessionManager.logout()

    @classmethod
    def current_user(cls):
        return SessionManager.get_user()

    @classmethod
    def role(cls):
        return SessionManager.get_role()

    @classmethod
    def is_authenticated(cls):
        return SessionManager.is_authenticated()