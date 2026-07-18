from __future__ import annotations

import pandas as pd
import streamlit as st

from services.api_client import APIClientError
from services.mentor_service import MentorService
from theme.theme import badge, card, empty_state, metric_card, render_timeline, section_header
from utils.session import SessionManager


def _mentor_id() -> int:
    return int((SessionManager.get_user() or {}).get("id", 2))


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, APIClientError):
        st.error(exc.user_message)
    else:
        st.error(f"Unable to load mentor data: {exc}")


def _mentees() -> list[dict]:
    return MentorService.mentees(_mentor_id())


def _mentee_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Employee", "Role", "Last Update", "Risk Score", "Risk", "Open Blockers", "Confidence"])
    return pd.DataFrame(
        [
            {
                "Employee": row["name"],
                "Role": row["role"],
                "Last Update": row["last_update"],
                "Risk Score": row["risk_score"],
                "Risk": row["risk"],
                "Open Blockers": row["open_blockers"],
                "Confidence": row["confidence"],
            }
            for row in rows
        ]
    )


def show_mentor_dashboard() -> None:
    user = SessionManager.get_user() or {}
    section_header("Mentor Dashboard", f"{user.get('name', 'Mentor')} can guide growth and keep feedback actionable.")
    try:
        mentees = _mentees()
    except Exception as exc:
        _handle_error(exc)
        return

    cols = st.columns(4)
    with cols[0]:
        metric_card("Mentees", str(len(mentees)), "Assigned", "info")
    with cols[1]:
        metric_card("High risk", str(len([m for m in mentees if m['risk'] == 'High'])), "Watch", "warning")
    with cols[2]:
        metric_card("Open blockers", str(sum(m["open_blockers"] for m in mentees)), "Live", "danger")
    with cols[3]:
        metric_card("Avg confidence", f"{sum(m['confidence'] for m in mentees) / max(len(mentees), 1):.1f}", "Backend", "success")

    st.subheader("Assigned mentees")
    st.dataframe(_mentee_frame(mentees), hide_index=True, width="stretch")
    if not mentees:
        empty_state("No assigned mentees", "Assigned mentees will appear here once available.")


def feedback_composer(employee: dict | None = None) -> None:
    st.subheader("Feedback composer")
    try:
        mentees = _mentees()
    except Exception as exc:
        _handle_error(exc)
        return
    if not mentees:
        empty_state("No assigned mentees", "Assigned mentees will appear here once available.")
        return
    selected = employee or st.selectbox("Mentee", mentees, format_func=lambda row: row["name"])
    with st.form(f"feedback_form_{selected['id']}"):
        kind = st.selectbox("Type", ["Praise", "Guidance", "Concern"])
        visibility = st.radio("Visibility", ["Employee only", "Employee and manager"], horizontal=True)
        message = st.text_area("Message", max_chars=1000, placeholder="Write specific, actionable feedback...")
        st.caption(f"{len(message)} / 1000 characters")
        sent = st.form_submit_button(f"Send feedback to {selected['name']}", type="primary", width="stretch")
    if sent:
        if len(message.strip()) < 10:
            st.error("Feedback must be at least 10 characters.")
            return
        try:
            response = MentorService.send_feedback({"employee_id": selected["id"], "type": kind, "message": message, "visibility": visibility})
            st.success(response.get("message", f"{kind} feedback sent to {selected['name']}."))
        except Exception as exc:
            _handle_error(exc)


def feedback_history(employee_id: int | None = None) -> None:
    try:
        mentees = _mentees()
        if not mentees:
            empty_state("No assigned mentees", "Assigned mentees will appear here once available.")
            return
        selected_id = employee_id or mentees[0]["id"]
        rows = MentorService.feedback(selected_id)
    except Exception as exc:
        _handle_error(exc)
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def show_mentees_page() -> None:
    section_header("Mentees", "Assigned mentees with current risk and update status.")
    try:
        mentees = _mentees()
    except Exception as exc:
        _handle_error(exc)
        return
    if not mentees:
        empty_state("No assigned mentees", "Assigned mentees will appear here once available.")
        return
    selected = st.selectbox("Select mentee", mentees, format_func=lambda row: row["name"])
    risk = MentorService.risk(selected["id"])
    updates = MentorService.updates(selected["id"])
    cols = st.columns(4)
    with cols[0]:
        metric_card("Risk score", str(risk["score"]), risk["label"], "warning")
    with cols[1]:
        metric_card("Confidence", str(selected["confidence"]), selected["risk_trend"], "info")
    with cols[2]:
        metric_card("Open blockers", str(selected["open_blockers"]), "Live", "danger")
    with cols[3]:
        metric_card("Last update", selected["last_update"], "Backend", "success")
    items = [
        {"label": "Daily update", "content": f"{row['created_at']} - {row['work_done']}", "status": "completed"}
        for row in updates
    ]
    if items:
        render_timeline(items)
    else:
        empty_state("No updates yet", "Updates for this mentee will appear here.")


def show_feedback_composer_page() -> None:
    section_header("Feedback Composer", "Send praise, guidance, or concern feedback.")
    feedback_composer()


def show_feedback_history_page() -> None:
    section_header("Feedback History", "Last 30 days of feedback.")
    feedback_history()
