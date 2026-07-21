from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from services.api_client import APIClientError
from services.manager_service import ManagerService
from theme.theme import badge, card, empty_state, metric_card, section_header, spacer, style_chart
from utils.session import SessionManager


def _get_team_id() -> str:
    user = SessionManager.get_user() or {}
    team_id = user.get("team_id")
    if not team_id:
        st.error("No active team assigned to manager context.")
        st.stop()
    return str(team_id)

def _handle_error(exc: Exception) -> None:
    if isinstance(exc, APIClientError):
        st.error(exc.user_message)
    else:
        st.error(f"Unable to load manager data: {exc}")


def _dashboard() -> dict | None:
    try:
        return ManagerService.dashboard()
    except Exception as exc:
        _handle_error(exc)
        return None


def _team_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Employee", "Last Update", "Risk Score", "Risk", "Risk Trend", "Open Blockers", "Overdue Tasks"])
    return pd.DataFrame(
        [
            {
                "Employee": row["name"],
                "Last Update": row["last_update"],
                "Risk Score": row["risk_score"],
                "Risk": row["risk"],
                "Risk Trend": row["risk_trend"],
                "Open Blockers": row["open_blockers"],
                "Overdue Tasks": row["overdue_tasks"],
            }
            for row in rows
        ]
    )


def _blocker_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Employee", "Blocker", "Severity", "Age", "Status"])
    return pd.DataFrame(
        [
            {
                "Employee": row["employee"],
                "Blocker": row["blocker"],
                "Severity": row["severity"],
                "Age": row["age"],
                "Status": row["status"],
            }
            for row in rows
        ]
    )


def _current_week_start() -> str:
    """Calculate the ISO date string for the current Monday (start of week)."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def _display_ai_summary_card(summary: dict | None) -> None:
    """Display an AI-generated summary in a card format."""
    if not summary:
        card(
            "Weekly Summary",
            "No summary available for this week.",
            badge_html=badge("No Data", "warning"),
        )
        return

    body = ""
    for section in ["highlights", "concerns", "recommendations"]:
        items = summary.get(section, [])
        if items:
            body += f"{section.title()}\n"
            body += "\n".join(f"- {item}" for item in items)
            body += "\n\n"

    if not body.strip():
        body = "Summary data is empty."

    card("Weekly Summary", body.strip(), badge_html=badge("AI Generated", "info"))


def _weekly_summary_card():
    """Display cached AI weekly summary in the main dashboard view."""
    week_start = _current_week_start()
    team_id = _get_team_id()
    try:
        summary = ManagerService.cached_weekly_summary(team_id, week_start)
    except Exception:
        card(
            "Weekly Summary",
            "Weekly summary is not available yet.",
            badge_html=badge("Info", "info"),
        )
        return

    _display_ai_summary_card(summary)

# ---------------------------------------------------------------------------
# Page Handlers (Imported by app.py)
# ---------------------------------------------------------------------------


def show_manager_dashboard() -> None:
    section_header("Manager Dashboard", "Team health, blockers, AI recommendations, and risk signals.")
    data = _dashboard()
    if not data:
        return
    kpis = data["kpis"]
    metrics = st.columns(5, gap="large")
    values = [
        ("Team Health Score", kpis["team_health"], "+4", "success"),
        ("High Risk Members", kpis["high_risk"], "Watch", "danger"),
        ("Open Blockers", kpis["open_blockers"], "Live", "warning"),
        ("Update Completion", f"{kpis['completion_rate']}%", "+6%", "info"),
        ("Unread Alerts", kpis["alerts"], "Review", "success"),
    ]
    for col, (label, value, delta, color) in zip(metrics, values):
        with col:
            metric_card(label, str(value), delta, color)

    spacer("md")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.subheader("Team risk overview")
        st.dataframe(_team_frame(data["employees"]), hide_index=True, width="stretch")
        st.subheader("Active blockers")
        st.dataframe(_blocker_frame(data["blockers"]), hide_index=True, width="stretch")
    with right:
        _weekly_summary_card()
        card("AI WorkLens Assistant", "Ask the assistant which blockers or employees need immediate intervention.", badge_html=badge("AI", "success"))


def show_team_risk_page() -> None:
    section_header("Team Risk", "Interactive risk table with filters and row-level actions.")
    data = _dashboard()
    if data:
        st.dataframe(_team_frame(data["employees"]), hide_index=True, width="stretch")
        if not data["employees"]:
            empty_state("No team data", "Team risk signals will appear after updates are available.")


def show_blockers_page() -> None:
    section_header("Active Blockers", "Track severity, age, status, ownership, and escalation.")
    data = _dashboard()
    if data:
        st.dataframe(_blocker_frame(data["blockers"]), hide_index=True, width="stretch")
        if not data["blockers"]:
            empty_state("No active blockers", "New blockers will appear here when reported.")


def show_ai_assistant_page() -> None:
    section_header("AI WorkLens Assistant", "Ask cited questions about delivery risk, blockers, and team health.")
    team_id = _get_team_id()
    history = SessionManager.get_chat()
    for item in history:
        with st.chat_message(item["role"]):
            st.write(item["message"])
    prompt = st.chat_input("Ask about risks, blockers, updates, or 1:1 prep...")
    if prompt:
        SessionManager.add_chat("user", prompt)
        try:
            response = ManagerService.ask_ai(prompt, team_id)
            answer = response.get("answer", "No response received.")
            # Parse sources with employee and date
            sources = response.get("sources", [])
            if sources:
                source_strs = []
                for s in sources:
                    employee = s.get("employee", "Unknown")
                    date = s.get("date", "N/A")
                    source_strs.append(f"{employee} ({date})")
                citations = "; ".join(source_strs)
            else:
                citations = "No specific sources"
            SessionManager.add_chat("assistant", f"{answer}\n\nSources: {citations}")
            st.rerun()
        except Exception as exc:
            _handle_error(exc)


def show_weekly_summary_page() -> None:
    section_header("Weekly Summary", "AI-generated highlights, concerns, and recommendations.")
    
    week_start = _current_week_start()
    team_id = _get_team_id()
    
    # Generate button
    if st.button("🔄 Generate Summary", type="primary"):
        with st.spinner("Generating AI summary..."):
            try:
                ManagerService.generate_weekly_summary(team_id, week_start)
                st.success("Summary generated successfully!")
                st.rerun()
            except Exception as exc:
                _handle_error(exc)
    
    # Display cached summary
    try:
        summary = ManagerService.cached_weekly_summary(team_id, week_start)
    except Exception:
        _display_ai_summary_card(None)
        return
    
    _display_ai_summary_card(summary)


def show_analytics_page() -> None:
    section_header("Analytics", "Team health trends, blockers, confidence, completion, and risk distribution.")
    try:
        team = ManagerService.team_analytics()
        blockers = ManagerService.blocker_analytics()
    except Exception as exc:
        _handle_error(exc)
        return
    
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("Team health trend")
        fig1 = px.line(x=team.get("labels", []), y=team.get("health_scores", []), markers=True, labels={"x": "Period", "y": "Health Score"})
        fig1.update_layout(height=300, showlegend=False)
        style_chart(fig1)
        st.plotly_chart(fig1, width="stretch")
    with c2:
        st.subheader("Blockers distribution")
        blocker_df = pd.DataFrame({
            "Status": ["Open", "Resolved", "Escalated"],
            "Count": [blockers.get("open", 0), blockers.get("resolved", 0), blockers.get("escalated", 0)]
        })
        fig2 = px.bar(blocker_df, x="Status", y="Count", color="Status")
        fig2.update_layout(height=300, showlegend=False)
        style_chart(fig2)
        st.plotly_chart(fig2, width="stretch")


def show_alerts_page() -> None:
    section_header("Alerts", "Prioritized notifications and risk events.")
    try:
        alerts = ManagerService.alerts()
    except Exception as exc:
        _handle_error(exc)
        return
    for item in alerts:
        alert_type = item.get("type", item.get("level", "Info"))
        card(alert_type, item["message"], badge_html=badge(alert_type, "danger" if alert_type == "Critical" else "info"))
    if not alerts:
        empty_state("No alerts", "Prioritized alerts will appear when new risk events are detected.")
