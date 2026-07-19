from __future__ import annotations

from typing import Any

import requests

from core.config import settings


def _request_json(url: str, params: dict | None = None, timeout: int = 30) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_ai_answer(question: str) -> str:
    payload = _request_json(
        f"{settings.API_BASE_URL}/ai/query/sync",
        params={"question": question},
    )
    return str(payload.get("answer", ""))
