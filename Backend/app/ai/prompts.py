"""
ai/prompts.py  — Member 3
All prompt templates in one place.
Import and call the builder functions from rag.py, summary_service.py, etc.
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """You are WorkLens AI, a work intelligence assistant for engineering managers.
You have access to real team update data retrieved from a vector database.

STRICT RULES:
1. ONLY make claims that are supported by text in the CONTEXT section below.
2. When citing an employee, ALWAYS include the date: example "Priya Sharma on Jan 12".
3. If the context does not contain enough information to answer, say exactly:
   "I don't have enough data to answer that — consider asking the employee directly."
4. Never fabricate risk scores, dates, or employee names.
5. Recommendations must be actionable and specific. Never say "consider talking to them" — say WHAT to discuss.
6. Output format: short paragraph of facts (with citations), then a numbered list of recommended actions."""


SUMMARY_SYSTEM_PROMPT = """You are WorkLens AI generating a weekly team summary for a manager.
Write in plain English. Maximum 200 words.
Structure your response with these three sections:
[Highlights], [Concerns], [Actions for next week].

Rules:
- Use employee first names only.
- Be specific — name the person, name the issue.
- Do NOT generalise. Do NOT say "some employees" — name them.
- If no concerns exist, say so explicitly."""


RECOMMENDATIONS_SYSTEM_PROMPT = """Generate EXACTLY 3 to 5 manager action items as a JSON array.

Format:
[
  {
    "priority": 1,
    "action": "...",
    "rationale": "...",
    "employee": "...",
    "urgency": "today | this_week | next_week"
  }
]

Priority 1 = most urgent.
Actions must be specific and executable within 1 working day.
Only output the JSON array. No preamble, no markdown code blocks."""


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_chat_messages(
    question: str,
    context_text: str,
    risk_json: list[dict],
) -> list[dict]:
    """
    Build the messages list for the RAG chat endpoint.

    Args:
        question:     Manager's natural language question.
        context_text: Pre-formatted string of retrieved update/blocker chunks.
        risk_json:    List of per-employee risk dicts from PostgreSQL.
    """
    user_content = f"""Team Update Context (retrieved from vector store — last 14 days):

{context_text}

## Structured Risk Data (from PostgreSQL)
{json.dumps(risk_json, indent=2, default=str)}

## Question
{question}"""

    return [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_summary_messages(
    team_name: str,
    week_label: str,
    employee_summaries: list[dict],
    risk_rows: list[dict],
    blocker_stats: dict,
) -> list[dict]:
    """
    Build the messages list for the weekly summary background job.

    Args:
        team_name:           e.g. "Platform Engineering"
        week_label:          e.g. "Jan 8–12, 2024"
        employee_summaries:  List of per-employee summary dicts.
        risk_rows:           End-of-week risk score rows.
        blocker_stats:       {opened, resolved, still_open} counts.
    """
    emp_block = "\n".join(
        f"- {e['full_name']}: {e['update_count']} updates. "
        f"Conf trend: {e['conf_start']}→{e['conf_end']}. "
        f"Open blockers: {e['open_blockers']}. "
        f"Notes: {e.get('notes', 'None')}."
        for e in employee_summaries
    )

    risk_block = " | ".join(
        f"{r['full_name']}: {r['label']} ({r['score']:.2f})"
        for r in risk_rows
    )

    user_content = f"""Week: {week_label} | Team: {team_name}

### Employee Updates Summary
{emp_block}

### End-of-Week Risk Scores
{risk_block}

### Blocker Stats
Opened: {blocker_stats['opened']} | Resolved: {blocker_stats['resolved']} | Still open: {blocker_stats['still_open']}"""

    return [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_recommendations_messages(
    context_text: str,
    risk_json: list[dict],
) -> list[dict]:
    """
    Build the messages list to generate structured JSON action items.
    """
    user_content = f"""Team Context:
{context_text}

Risk Data:
{json.dumps(risk_json, indent=2, default=str)}

Generate 3-5 prioritised manager action items."""

    return [
        {"role": "system", "content": RECOMMENDATIONS_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# Context builder helper (used by rag.py)
# ---------------------------------------------------------------------------

def build_context_string(hydrated_chunks: list[dict]) -> str:
    """
    Convert a list of hydrated RAG chunks into the formatted context string
    that gets injected into the prompt.

    Each chunk dict must have: full_name, date, text, doc_type
    """
    # Group by employee
    by_employee: dict[str, list[dict]] = {}
    for chunk in hydrated_chunks:
        name = chunk["full_name"]
        by_employee.setdefault(name, []).append(chunk)

    sections: list[str] = []
    for name, chunks in by_employee.items():
        # Sort by date ascending so the narrative reads chronologically
        chunks.sort(key=lambda c: c["date"])
        header = f"### {name}"
        lines = [header]
        for c in chunks:
            lines.append(c["text"])
        sections.append("\n".join(lines))

    return "\n\n".join(sections)