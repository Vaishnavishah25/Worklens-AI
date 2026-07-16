"""
ai/llm.py  — Member 3  (Ollama version)
"""
from __future__ import annotations
import os
import json
import re
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = "gemma3:4b"
TEMPERATURE = 0.05
USE_OLLAMA = os.getenv("WORKLENS_USE_OLLAMA", "0") == "1"

async def stream_chat(messages: list[dict]):
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

                # ✅ Initialize here
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

                # Optional: print or save the complete response
                print(full_response)

    except Exception as e:
        print(f"Ollama Error: {e}")
        yield _fallback_response(messages)


async def complete(messages: list[dict], max_tokens: int = 600) -> str:
    """Non-streaming — returns the full response string."""
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


def _fallback_response(messages: list[dict]) -> str:
    """Small extractive fallback so the app still works without Ollama."""
    system_text = messages[0].get("content", "") if messages else ""
    user_text = messages[-1].get("content", "") if messages else ""

    if "JSON array" in system_text:
        return _fallback_recommendations(user_text)
    if "weekly team summary" in system_text.lower() or "weekly summary" in user_text.lower():
        return _fallback_summary(user_text)
    return _fallback_chat(user_text)


def _extract_context(user_text: str) -> str:
    match = re.search(
        r"Team Update Context.*?:\s*(.*?)\n\s*## Structured Risk Data",
        user_text,
        flags=re.S,
    )
    if match:
        return match.group(1).strip()
    match = re.search(r"Team Context:\s*(.*?)\n\s*Risk Data:", user_text, flags=re.S)
    if match:
        return match.group(1).strip()
    match = re.search(r"Recent Updates from FAISS:\s*(.*?)\n\nGenerate", user_text, flags=re.S)
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
        if any(word in lower for word in ("blocker", "blocked", "waiting", "risk", "confidence", "feedback")):
            score += 1
        scored.append((score, line))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [line for score, line in scored if score > 0][:limit]
    return selected or lines[:limit]


def _fallback_chat(user_text: str) -> str:
    context = _extract_context(user_text)
    question = _extract_question(user_text)
    if not context:
        return "I don't have enough data to answer that - consider asking the employee directly."

    lines = _relevant_lines(context, question)
    facts = "\n".join(lines[:3])
    actions = [
        "Review the named blocker and assign a clear owner today.",
        "Ask the employee for the next concrete unblock step and expected date.",
        "Use the cited update dates as the source of truth when following up.",
    ]
    return facts + "\n\nRecommended actions:\n" + "\n".join(
        f"{idx}. {action}" for idx, action in enumerate(actions, start=1)
    )


def _fallback_summary(user_text: str) -> str:
    context = _extract_context(user_text)
    lines = _relevant_lines(context, "highlights blockers confidence completed", limit=6)
    blocker_lines = [line for line in lines if "blocker" in line.lower() or "waiting" in line.lower()]
    highlight_lines = [line for line in lines if line not in blocker_lines]
    return (
        "[Highlights]\n"
        + "\n".join(f"- {line}" for line in (highlight_lines[:2] or lines[:2]))
        + "\n\n[Concerns]\n"
        + "\n".join(f"- {line}" for line in (blocker_lines[:2] or ["No explicit blocker concerns found in the retrieved context."]))
        + "\n\n[Actions for next week]\n"
        "- Escalate open blockers with named owners.\n"
        "- Use recent confidence and update notes to plan focused 1:1s."
    )


def _fallback_recommendations(user_text: str) -> str:
    context = _extract_context(user_text)
    lines = _relevant_lines(context, "blocker risk confidence urgent", limit=3)
    names = []
    for line in lines:
        match = re.search(r"\[([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\]", line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    while len(names) < 3:
        names.append("Team")
    payload = [
        {
            "priority": 1,
            "action": f"Resolve the highest-impact blocker for {names[0]}.",
            "rationale": lines[0] if lines else "Retrieved context indicates blocker or confidence risk.",
            "employee": names[0],
            "urgency": "today",
        },
        {
            "priority": 2,
            "action": f"Run a focused 1:1 with {names[1]} on next steps and confidence.",
            "rationale": lines[1] if len(lines) > 1 else "Recent updates should be reviewed with the employee.",
            "employee": names[1],
            "urgency": "this_week",
        },
        {
            "priority": 3,
            "action": "Review open work and assign owners for unresolved dependencies.",
            "rationale": lines[2] if len(lines) > 2 else "Team context contains work that needs manager follow-up.",
            "employee": names[2],
            "urgency": "this_week",
        },
    ]
    return json.dumps(payload)
