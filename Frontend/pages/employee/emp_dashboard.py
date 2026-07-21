from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from services.api_client import APIClientError
from services.employee_service import EmployeeService
from theme.theme import badge, card, empty_state, hero_card, metric_card, render_timeline, section_header, style_chart
from utils.session import SessionManager


def _user_id() -> int:
    user = SessionManager.get_user() or {}
    user_id = user.get("id")
    if not user_id:
        st.error("Session expired. Please log in again.")
        st.stop()
    return int(user_id)


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, APIClientError):
        st.error(exc.user_message)
    else:
        st.error(f"Unable to load employee data: {exc}")


def _task_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Task", "Due", "Status", "Risk"])
    return pd.DataFrame(
        [
            {
                "Task": row.get("task", row.get("title", "Untitled")),
                "Due": row.get("due", row.get("due_date", "N/A")),
                "Status": row.get("status", "todo"),
                "Risk": row.get("risk", "Low"),
            }
            for row in rows
        ]
    )


def show_employee_dashboard() -> None:
    user = SessionManager.get_user() or {}
    name = user.get("name", "there")
    employee_id = _user_id()
    section_header("Employee Workspace", f"Welcome back, {name}. Keep momentum high and surface blockers early.")

    try:
        risk = EmployeeService.risk(employee_id) or {"score": 0, "label": "LOW", "factors": []}
        tasks = EmployeeService.tasks(employee_id) or []
        feedback = EmployeeService.feedback(employee_id) or []
    except Exception as exc:
        _handle_error(exc)
        return

    # Handle 404 as expected normal state (no update submitted today)
    today = EmployeeService.today_update()

    col_a, col_b = st.columns([2.3, 1], gap="large")
    with col_a:
        hero_card("Good morning", "Your updates, blockers, and confidence signals are visible to your support circle.", "Today")
    with col_b:
        if today:
            card("Daily update", "Submitted today", badge_html=badge("Live", "success"))
        else:
            card("Daily update", "No update submitted yet", badge_html=badge("Pending", "warning"))
    
    # Show info message if no update submitted today
    if today is None:
        st.info("📅 You haven't submitted your daily update for today yet.")
        if st.button("📝 Submit Today's Update", type="primary"):
            st.session_state["navigate_to"] = "daily_update"
            st.rerun()

    cols = st.columns(4)
    with cols[0]:
        metric_card("Tasks", str(len(tasks)), "From backend", "info")
    with cols[1]:
        metric_card("Confidence", str(today.get("confidence", "-") if today else "-"), "Latest update", "warning")
    with cols[2]:
        metric_card("Current risk", str(risk["score"]), risk["label"], "info")
    with cols[3]:
        metric_card("Feedback", str(len(feedback)), "Inbox", "success")

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.subheader("Tasks")
        st.dataframe(_task_frame(tasks), hide_index=True, width="stretch")
    with right:
        risk_label = risk.get("label", "LOW")
        card("Risk transparency", "\n".join(f"- {factor}" for factor in risk.get("factors", [])), badge_html=badge(risk["label"], risk["label"].lower()))
        st.subheader("Recent feedback")
        for item in feedback[:3]:
            card(item["from"], item["message"], eyebrow=item["date"], badge_html=badge(item["type"], "info"))
        if not feedback:
            empty_state("No feedback yet", "Feedback from mentors and managers will appear here.")


def show_daily_update() -> None:
    section_header("Daily Update", "Capture work done, blockers, next steps, and confidence.")

    with st.form("daily_update_form"):
        work_done = st.text_area("Work Done", placeholder="What did you complete or make progress on today?", height=130)
        no_blockers = st.checkbox("No blockers today")
        blocker = st.text_area("Blockers", placeholder="What is blocking or slowing you down?", height=100, disabled=no_blockers)
        severity = st.segmented_control("Severity", ["None", "Low", "Medium", "High", "Critical"], default="None")
        next_steps = st.text_area("Next Steps", placeholder="What are you planning to do next?", height=100)
        confidence = st.slider("Confidence", min_value=1, max_value=5, value=4)
        submitted = st.form_submit_button("Submit update", type="primary", width="stretch")

    if submitted:
        if not work_done.strip() or not next_steps.strip():
            st.error("Please complete Work Done and Next Steps before submitting.")
            return
        if severity != "None" and not no_blockers and not blocker.strip():
            st.error("Please describe the blocker or select 'No blockers today'.")
            return
        payload = {
            "work_done": work_done,
            "blockers": "" if no_blockers else blocker,
            "severity": severity,
            "next_steps": next_steps,
            "confidence": confidence,
        }
        try:
            result = EmployeeService.submit_update(payload)
            SessionManager.save_daily_update({**payload, "submitted_at": datetime.now().strftime("%I:%M %p")})
            assigned_risk = result.get("risk_assigned", result.get("label", "Success"))
            st.success(f"Update submitted. Risk status: {assigned_risk}.")
        except Exception as exc:
            _handle_error(exc)


def show_my_tasks() -> None:
    section_header("My Tasks", "Review overdue, in-progress, and completed work.")
    try:
        tasks = _task_frame(EmployeeService.tasks(_user_id()))
    except Exception as exc:
        _handle_error(exc)
        return
    for status in ["Overdue", "In Progress", "Completed"]:
        st.subheader(status)
        rows = tasks[tasks["Status"] == status]
        if rows.empty:
            empty_state(f"No {status.lower()} tasks", "This section will update when matching tasks are available.")
        else:
            st.dataframe(rows, hide_index=True, width="stretch")


def show_progress_timeline() -> None:
    section_header("Progress Timeline", "A chronological view of updates, confidence, blockers, and feedback.")
    try:
        updates = EmployeeService.updates(_user_id())
    except Exception as exc:
        _handle_error(exc)
        return
    items = [
        {"label": "Daily update", "content": f"{row['created_at']} - {row['work_done']} - Confidence {row['confidence']}", "status": "completed"}
        for row in updates
    ]
    if items:
        render_timeline(items)
    else:
        empty_state("No updates yet", "Submit daily updates to build your progress timeline.")


def show_feedback_inbox() -> None:
    section_header("Feedback Inbox", "Review praise, guidance, and concerns from mentors and managers.")
    try:
        feedback = EmployeeService.feedback(_user_id())
    except Exception as exc:
        _handle_error(exc)
        return
    for item in feedback:
        card(item["from"], item["message"], eyebrow=item["date"], badge_html=badge(item["type"], "info"))
    if not feedback:
        empty_state("No feedback yet", "Feedback from mentors and managers will appear here.")


def show_my_risk() -> None:
    section_header("My Risk", "Transparent, explainable risk scoring focused on support.")
    try:
        emp_id = _user_id()
        risk = EmployeeService.risk(emp_id) or {"score": 0, "label": "LOW", "factors": []}
        updates = EmployeeService.updates(emp_id) or []
    except Exception as exc:
        _handle_error(exc)
        return
    
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        card(
            "Risk Score",
            f"{risk.get('score', 0)} / 100\n" + "\n".join(f"- {factor}" for factor in risk.get("factors", [])),
            badge_html=badge(risk_label, risk_label.lower()),
        )
    with right:
        st.subheader("Confidence Trend")
        if updates:
            frame = pd.DataFrame(updates)
            y_col = "confidence" if "confidence" in frame.columns else "confidence_score"
            if y_col in frame.columns and "created_at" in frame.columns:
                fig = px.line(frame, x="created_at", y=y_col, markers=True, labels={y_col: "Confidence"})
                fig.update_layout(height=300, showlegend=False)
                style_chart(fig)
                st.plotly_chart(fig, width="stretch")
            else:
                empty_state("Data pending", "Confidence data will render on your next update.")
        else:
            empty_state("No trend yet", "Submit updates to build a confidence trend.")
