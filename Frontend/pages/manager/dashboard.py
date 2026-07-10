from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from services.api_client import APIClientError
from services.manager_service import ManagerService
from theme.theme import badge, card, empty_state, metric_card, section_header, spacer, style_chart
from utils.session import SessionManager


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


def _weekly_summary_card() -> None:
    try:
        summary = ManagerService.weekly_summary()
    except Exception as exc:
        _handle_error(exc)
        return
    body = ""
    for section in ["highlights", "concerns", "recommendations"]:
        body += f"{section.title()}\n"
        body += "\n".join(f"- {item}" for item in summary.get(section, []))
        body += "\n\n"
    card("Weekly Summary", body, badge_html=badge("AI Generated", "info"))


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
        st.dataframe(_team_frame(data["employees"]), hide_index=True, use_container_width=True)
        st.subheader("Active blockers")
        st.dataframe(_blocker_frame(data["blockers"]), hide_index=True, use_container_width=True)
    with right:
        _weekly_summary_card()
        card("AI WorkLens Assistant", "Ask the assistant which blockers or employees need immediate intervention.", badge_html=badge("AI", "success"))


def show_team_risk_page() -> None:
    section_header("Team Risk", "Interactive risk table with filters and row-level actions.")
    data = _dashboard()
    if data:
        st.dataframe(_team_frame(data["employees"]), hide_index=True, use_container_width=True)
        if not data["employees"]:
            empty_state("No team data", "Team risk signals will appear after updates are available.")


def show_blockers_page() -> None:
    section_header("Active Blockers", "Track severity, age, status, ownership, and escalation.")
    data = _dashboard()
    if data:
        st.dataframe(_blocker_frame(data["blockers"]), hide_index=True, use_container_width=True)
        if not data["blockers"]:
            empty_state("No active blockers", "New blockers will appear here when reported.")


def show_ai_assistant_page() -> None:
    section_header("AI WorkLens Assistant", "Ask cited questions about delivery risk, blockers, and team health.")
    history = SessionManager.get_chat()
    for item in history:
        with st.chat_message(item["role"]):
            st.write(item["message"])
    prompt = st.chat_input("Ask about risks, blockers, updates, or 1:1 prep...")
    if prompt:
        SessionManager.add_chat("user", prompt)
        try:
            response = ManagerService.ask_ai(prompt)
            answer = response["answer"]
            citations = "; ".join(f"{c['title']} ({c['source']})" for c in response.get("citations", []))
            SessionManager.add_chat("assistant", f"{answer}\n\nSources: {citations}")
            st.rerun()
        except Exception as exc:
            _handle_error(exc)


def show_weekly_summary_page() -> None:
    section_header("Weekly Summary", "AI-generated highlights, concerns, and recommendations.")
    _weekly_summary_card()


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
        fig = px.line(x=team["labels"], y=team["health"], markers=True, labels={"x": "Day", "y": "Health"})
        fig.update_layout(height=300, showlegend=False)
        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Risk distribution")
        fig = px.pie(names=list(team["risk_distribution"].keys()), values=list(team["risk_distribution"].values()), hole=.58)
        fig.update_layout(height=300)
        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Blockers per week")
    fig = px.bar(pd.DataFrame({"Week": blockers["labels"], "Blockers": blockers["counts"]}), x="Week", y="Blockers")
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)


def show_alerts_page() -> None:
    section_header("Alerts", "Prioritized notifications and risk events.")
    try:
        alerts = ManagerService.alerts()
    except Exception as exc:
        _handle_error(exc)
        return
    for item in alerts:
        card(item["level"], item["message"], badge_html=badge(item["level"], "danger" if item["level"] == "Critical" else "info"))
    if not alerts:
        empty_state("No alerts", "Prioritized alerts will appear when new risk events are detected.")
