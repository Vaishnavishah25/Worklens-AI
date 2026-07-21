# frontend/pages/mentor/mentor_dashboard.py

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.api_client import APIClientError
from services.mentor_service import MentorService
from theme.theme import badge, card, empty_state, metric_card, render_timeline, section_header
from utils.session import SessionManager


def _mentor_id() -> int:
    user = SessionManager.get_user() or {}
    mentor_id = user.get("id")
    if not mentor_id:
        st.error("Session expired or missing user context.")
        st.stop()
    return int(mentor_id)


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
                "Employee": row.get("name", "Unknown"),
                "Role": row.get("role", "employee"),
                "Last Update": row.get("last_update", "N/A"),
                "Risk Score": row.get("risk_score", 0),
                "Risk": row.get("risk", "LOW"),
                "Open Blockers": row.get("open_blockers", 0),
                "Confidence": row.get("confidence", "N/A"),
            }
            for row in rows
        ]
    )


def show_mentor_dashboard() -> None:
    user = SessionManager.get_user() or {}
    section_header("Mentor Dashboard", f"{user.get('name', 'Mentor')} — Guide growth and keep feedback actionable.")
    try:
        mentees = _mentees()
    except Exception as exc:
        _handle_error(exc)
        return

    cols = st.columns(4)
    with cols[0]:
        metric_card("Mentees", str(len(mentees)), "Assigned", "info")
    with cols[1]:
        high_risk_count = len([m for m in mentees if str(m.get('risk', '')).upper() == 'HIGH'])
        metric_card("High risk", str(high_risk_count), "Watch", "warning")
    with cols[2]:
        open_blockers = sum(m.get("open_blockers", 0) for m in mentees)
        metric_card("Open blockers", str(open_blockers), "Live", "danger")
    with cols[3]:
        conf_values = [m.get("confidence", 0) for m in mentees if isinstance(m.get("confidence"), (int, float))]
        avg_conf = (sum(conf_values) / max(len(conf_values), 1)) if conf_values else 0.0
        metric_card("Avg confidence", f"{avg_conf:.1f}", "Backend", "success")

    st.subheader("Assigned mentees")
    st.dataframe(_mentee_frame(mentees), hide_index=True, width="stretch")
    if not mentees:
        empty_state("No assigned mentees", "Assigned mentees will appear here once available.")


FEEDBACK_TYPE_MAP = {"Praise": "praise", "Guidance": "guidance", "Concern": "concern"}
FEEDBACK_VISIBILITY_MAP = {"Employee only": "employee_only", "Employee and manager": "manager_only"}


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

    selected = employee or st.selectbox("Mentee", mentees, format_func=lambda row: row.get("name", "Unknown"))
    with st.form(f"feedback_form_{selected.get('id')}"):
        kind = st.selectbox("Type", ["Praise", "Guidance", "Concern"])
        visibility = st.radio("Visibility", ["Employee only", "Employee and manager"], horizontal=True)
        message = st.text_area("Message", max_chars=1000, placeholder="Write specific, actionable feedback...")
        st.caption(f"{len(message)} / 1000 characters")
        sent = st.form_submit_button(f"Send feedback to {selected.get('name', 'Mentee')}", type="primary", width="stretch")

    if sent:
        if len(message.strip()) < 10:
            st.error("Feedback must be at least 10 characters.")
            return
        try:
            payload = {
                "mentee_id": selected["id"],
                "type": FEEDBACK_TYPE_MAP.get(kind, kind.lower()),
                "message": message.strip(),
                "visibility": FEEDBACK_VISIBILITY_MAP.get(visibility, "employee_only")
            }
            response = MentorService.send_feedback(payload)
            st.success(response.get("message", f"{kind} feedback sent to {selected.get('name')}."))
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

    if not rows:
        empty_state("No feedback history", "Sent feedback items will appear here.")
    else:
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

    selected = st.selectbox("Select mentee", mentees, format_func=lambda row: row.get("name", "Unknown"))
    risk = MentorService.risk(selected["id"])
    updates = MentorService.updates(selected["id"])

    cols = st.columns(4)
    with cols[0]:
        metric_card("Risk score", str(risk.get("score", 0)), risk.get("label", "LOW"), "warning")
    with cols[1]:
        metric_card("Confidence", str(selected.get("confidence", "N/A")), selected.get("risk_trend", "Stable"), "info")
    with cols[2]:
        metric_card("Open blockers", str(selected.get("open_blockers", 0)), "Live", "danger")
    with cols[3]:
        metric_card("Last update", str(selected.get("last_update", "N/A")), "Backend", "success")

    items = [
        {"label": "Daily update", "content": f"{row.get('created_at', '')} - {row.get('work_done', '')}", "status": "completed"}
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
    section_header("Feedback History", "Review past feedback entries.")
    feedback_history()