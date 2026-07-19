"""
test/test_llm.py
Tests ai/llm.py — run with: python -m pytest test/test_llm.py -v
Requires Ollama running at localhost:11434 with llama3.1:8b pulled.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Backend', 'app'))

import pytest
from ai.llm import stream_chat, complete, CHAT_MODEL, OLLAMA_BASE_URL


# ── Config check ─────────────────────────────────────────────────────────────

def test_config_values():
    assert OLLAMA_BASE_URL == "http://localhost:11434"
    assert CHAT_MODEL == "llama3.1:8b"
    print(f"\nOLLAMA URL: {OLLAMA_BASE_URL}")
    print(f"CHAT MODEL: {CHAT_MODEL}")


# ── Non-streaming complete() ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_returns_string():
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Answer in one sentence only."},
        {"role": "user", "content": "What is 2 + 2?"},
    ]
    result = await complete(messages, max_tokens=50)
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"\nCOMPLETE RESPONSE: {result}")


@pytest.mark.asyncio
async def test_complete_follows_system_prompt():
    messages = [
        {"role": "system", "content": "You must respond with ONLY the word YES or NO. Nothing else."},
        {"role": "user", "content": "Is Python a programming language?"},
    ]
    result = await complete(messages, max_tokens=10)
    assert "YES" in result.upper() or "NO" in result.upper()
    print(f"\nSYSTEM PROMPT FOLLOWED: '{result.strip()}'")


@pytest.mark.asyncio
async def test_complete_json_output():
    messages = [
        {
            "role": "system",
            "content": 'Respond ONLY with valid JSON. No explanation. Format: {"answer": "...", "confidence": 0-10}',
        },
        {"role": "user", "content": "Is the sky blue?"},
    ]
    import json
    result = await complete(messages, max_tokens=100)
    clean = result.strip().strip("```json").strip("```").strip()
    parsed = json.loads(clean)
    assert "answer" in parsed
    print(f"\nJSON OUTPUT: {parsed}")


# ── Streaming stream_chat() ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_chat_yields_chunks():
    messages = [
        {"role": "system", "content": "You are helpful. Answer briefly."},
        {"role": "user", "content": "Say hello in 5 words."},
    ]
    chunks = []
    async for chunk in stream_chat(messages):
        assert isinstance(chunk, str)
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert len(chunks) > 0
    assert len(full_response) > 0
    print(f"\nSTREAMING CHUNKS RECEIVED: {len(chunks)}")
    print(f"FULL RESPONSE: {full_response}")


@pytest.mark.asyncio
async def test_stream_chat_assembles_correctly():
    messages = [
        {"role": "system", "content": "Answer in exactly one sentence."},
        {"role": "user", "content": "What is machine learning?"},
    ]
    full = ""
    async for chunk in stream_chat(messages):
        full += chunk

    assert len(full) > 20
    print(f"\nASSEMBLED RESPONSE ({len(full)} chars): {full[:100]}...")


@pytest.mark.asyncio
async def test_complete_worklens_style_prompt():
    """Tests the actual prompt style used by WorkLens AI."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are WorkLens AI. Only use data from the CONTEXT section. "
                "Format: one paragraph of facts, then numbered actions."
            ),
        },
        {
            "role": "user",
            "content": (
                "CONTEXT:\n"
                "Priya Sharma 2024-01-14: Blocked on staging env for 3 days. Confidence: 5/10.\n\n"
                "QUESTION:\nWhy is Priya delayed?"
            ),
        },
    ]
    result = await complete(messages, max_tokens=200)
    assert "Priya" in result
    assert len(result) > 30
    print(f"\nWORKLENS STYLE RESPONSE:\n{result}")