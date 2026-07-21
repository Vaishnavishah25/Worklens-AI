# ai/llm.py — Supports Z.AI / GLM API with token limits & Ollama/Fallback
from __future__ import annotations
import os
import json
import re
import httpx

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/paas/v4/")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-5")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = "gemma3:4b"
TEMPERATURE = 0.05
USE_OLLAMA = os.getenv("WORKLENS_USE_OLLAMA", "0") == "1"


async def stream_chat(messages: list[dict]):
    """Stream chat responses via GLM API or fallback to local extractor."""
    if LLM_PROVIDER == "glm" and GLM_API_KEY:
        async for chunk in _stream_glm(messages):
            yield chunk
        return

    if not USE_OLLAMA:
        yield _fallback_response(messages)
        return

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": TEMPERATURE,
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_ctx": 8192,
                        "num_predict": 512,
                    },
                },
            ) as response:
                response.raise_for_status()
                full_response = ""
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        full_response += chunk
                        yield chunk
                    if data.get("done"):
                        break
    except Exception as e:
        print(f"Ollama Stream Error: {e}")
        yield _fallback_response(messages)


async def _stream_glm(messages: list[dict]):
    """OpenAI-compatible streaming client for Z.AI / GLM."""
    url = f"{GLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GLM_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": TEMPERATURE,
        "max_tokens": 512,  # Strict token limit for cost control
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        delta = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"GLM Stream Error: {e}")
        yield _fallback_response(messages)


async def complete(messages: list[dict], max_tokens: int = 600) -> str:
    """Non-streaming — returns full response string with strict token ceiling."""
    if LLM_PROVIDER == "glm" and GLM_API_KEY:
        return await _complete_glm(messages, max_tokens)

    if not USE_OLLAMA:
        return _fallback_response(messages)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": TEMPERATURE,
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1,
                        "num_ctx": 8192,
                        "num_predict": max_tokens
                    },
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
    except Exception:
        return _fallback_response(messages)


async def _complete_glm(messages: list[dict], max_tokens: int = 600) -> str:
    """Non-streaming client for Z.AI / GLM."""
    url = f"{GLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GLM_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": TEMPERATURE,
        "max_tokens": max_tokens,  # Enforces paid limit ceiling
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"GLM Completion Error: {e}")
        return _fallback_response(messages)


def _fallback_response(messages: list[dict]) -> str:
    """Extractive fallback if API key fails or network drops."""
    system_text = messages[0].get("content", "") if messages else ""
    user_text = messages[-1].get("content", "") if messages else ""

    if "JSON array" in system_text:
        return _fallback_recommendations(user_text)
    if "weekly team summary" in system_text.lower() or "weekly summary" in user_text.lower():
        return _fallback_summary(user_text)
    return _fallback_chat(user_text)


def _extract_context(user_text: str) -> str:
    match = re.search(r"Team Update Context.*?:\s*(.*?)\n\s*## Structured Risk Data", user_text, flags=re.S)
    if match:
        return match.group(1).strip()
    match = re.search(r"Team Context:\s*(.*?)\n\s*Risk Data:", user_text, flags=re.S)
    if match:
        return match.group(1).strip()
    return user_text.strip()


def _extract_question(user_text: str) -> str:
    match = re.search(r"## Question\s*(.*)", user_text, flags=re.S)
    return match.group(1).strip() if match else ""


def _relevant_lines(context: str, question: str, limit: int = 5) -> list[str]:
    lines = [line.strip() for line in context.splitlines() if line.strip() and not line.startswith("###")]
    terms = [term for term in re.findall(r"[a-zA-Z]+", question.lower()) if len(term) > 2]
    scored: list[tuple[int, str]] = []
    for line in lines:
        lower = line.lower()
        score = sum(1 for term in terms if term in lower)
        scored.append((score, line))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [line for score, line in scored if score > 0][:limit]
    return selected or lines[:limit]


def _fallback_chat(user_text: str) -> str:
    context = _extract_context(user_text)
    question = _extract_question(user_text)
    if not context:
        return "I don't have enough data to answer that — consider asking the employee directly."
    lines = _relevant_lines(context, question)
    return "\n".join(lines[:3]) + "\n\nRecommended actions:\n1. Review the blocker today.\n2. Follow up in 1:1."


def _fallback_summary(user_text: str) -> str:
    return "[Highlights]\n- Team active.\n\n[Concerns]\n- Review open blockers.\n\n[Actions for next week]\n- Plan 1:1s."


def _fallback_recommendations(user_text: str) -> str:
    payload = [
        {
            "priority": 1,
            "action": "Review high-risk team blockers.",
            "rationale": "Retrieved context indicates active delivery risk.",
            "employee": "Team",
            "urgency": "today",
        }
    ]
    return json.dumps(payload)