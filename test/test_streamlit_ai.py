from __future__ import annotations

from streamlit_app import get_ai_answer


def test_get_ai_answer_returns_backend_answer(monkeypatch):
    def fake_request_json(url: str, params: dict | None = None, timeout: int = 30):
        assert url.endswith("/api/v1/ai/query/sync")
        assert params is not None
        assert params["question"] == "Who needs help?"
        return {"answer": "Anita needs help", "sources": [], "latency_ms": 12}

    monkeypatch.setattr("streamlit_app._request_json", fake_request_json)

    assert get_ai_answer("Who needs help?") == "Anita needs help"
