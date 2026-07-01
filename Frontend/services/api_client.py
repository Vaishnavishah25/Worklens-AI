from __future__ import annotations

from typing import Any

import requests
import streamlit as st
from core.config import settings

class APIClientError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    @property
    def user_message(self) -> str:
        labels = {
            0: "Backend unavailable. Start FastAPI on http://localhost:8000.",
            401: "Your session is invalid or credentials are incorrect.",
            403: "You do not have permission to perform this action.",
            404: "The requested WorkLens record was not found.",
            422: "Some submitted fields need attention.",
            500: "The WorkLens API hit an unexpected error.",
        }
        prefix = labels.get(self.status_code, "Request failed.")
        return f"{prefix} {self.message}"


class APIClient:
    BASE_URL = settings.API_BASE_URL
    TIMEOUT = 20

    @classmethod
    def _headers(cls, include_auth: bool = True) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        token = st.session_state.get("access_token")
        if include_auth and token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def _request(cls, method, endpoint, payload: None = None, include_auth= True, **kwargs):
        try:
            response = requests.request(
                method,
                f"{cls.BASE_URL}{endpoint}",
                headers=cls._headers(include_auth),
                json=payload,
                timeout=cls.TIMEOUT,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise APIClientError(0, str(exc)) from exc

        if response.status_code == 401 and include_auth:
            if cls._try_refresh():
                response = requests.request(
                    method,f"{cls.BASE_URL}{endpoint}",
                    headers=cls._headers(include_auth=True),
                    json=payload,timeout=cls.TIMEOUT,**kwargs
                )
            else:
                SessionManager.logout()
                st.rerun()

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise APIClientError(response.status_code, str(detail))

        if not response.text:
            return None
        return response.json()
    
    @classmethod
    def _try_refresh(cls)-> bool:
        token = st.session_state.get("refresh_token")
        if not token:
            return False
        try:
            resp = requests.port(
                f"{cls.BASE_URL}/auth/refresh",
                json = {"refresh_token":token},
                timeout =10,
            )
            if resp.status_code == 200:
                st.session_state.access_token = resp.json()["access_token"]
                return True
        except Exception:
            pass
        return False

    @classmethod
    def get(cls, endpoint: str, **kwargs):
        return cls._request("GET", endpoint, **kwargs)

    @classmethod
    def post(cls, endpoint: str, payload: dict | None = None, **kwargs):
        return cls._request("POST", endpoint, payload=payload, **kwargs)

    @classmethod
    def put(cls, endpoint: str, payload: dict | None = None, **kwargs):
        return cls._request("PUT", endpoint, payload=payload, **kwargs)

    @classmethod
    def delete(cls, endpoint: str, **kwargs):
        return cls._request("DELETE", endpoint, **kwargs)
