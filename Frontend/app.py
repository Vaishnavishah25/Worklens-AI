from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import streamlit as st

from auth.login import show_login
from pages.employee.dashboard import (
    show_daily_update,
    show_employee_dashboard,
    show_feedback_inbox,
    show_my_risk,
    show_my_tasks,
    show_progress_timeline,
)
from pages.manager.dashboard import (
    show_ai_assistant_page,
    show_alerts_page,
    show_analytics_page,
    show_blockers_page,
    show_manager_dashboard,
    show_team_risk_page,
    show_weekly_summary_page,
)
from pages.mentor.dashboard import (
    show_feedback_composer_page,
    show_feedback_history_page,
    show_mentees_page,
    show_mentor_dashboard,
)
from theme.theme import load_theme
from utils.session import SessionManager


APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "logo.png"

RouteHandler = Callable[[], None]

ROUTES: dict[str, dict[str, RouteHandler]] = {
    "employee": {
        "Dashboard": show_employee_dashboard,
        "Daily Update": show_daily_update,
        "My Tasks": show_my_tasks,
        "Progress Timeline": show_progress_timeline,
        "Feedback Inbox": show_feedback_inbox,
        "My Risk": show_my_risk,
    },
    "mentor": {
        "Dashboard": show_mentor_dashboard,
        "Mentees": show_mentees_page,
        "Feedback Composer": show_feedback_composer_page,
        "Feedback History": show_feedback_history_page,
    },
    "manager": {
        "Dashboard": show_manager_dashboard,
        "Team Risk": show_team_risk_page,
        "Blockers": show_blockers_page,
        "AI Assistant": show_ai_assistant_page,
        "Weekly Summary": show_weekly_summary_page,
        "Analytics": show_analytics_page,
        "Alerts": show_alerts_page,
    },
}

ROLE_LABELS = {
    "employee": "Employee",
    "mentor": "Mentor",
    "manager": "Manager",
}

def normalize_role(role: str | None) -> str:
    role = (role or "").strip().lower()
    return role if role in ROUTES else ""


def default_page_for(role: str) -> str:
    return next(iter(ROUTES[role]))


def current_page_for(role: str) -> str:
    page = SessionManager.get_page()
    if page not in ROUTES[role]:
        page = default_page_for(role)
        SessionManager.set_page(page)
    return page


def hide_streamlit_sidebar():
    pass
    #st.markdown(
      #  """
     #   <style>
     #   [data-testid="stSidebar"], [data-testid="collapsedControl"] {
     #       display: none;
      #  }
      #  .block-container {
       #     max-width: 1280px;
     #   }
      #  </style>
      #  """,
      #  unsafe_allow_html=True,
   # )


def render_logo_header() -> None:
    if LOGO_PATH.exists():
        logo_col, title_col = st.columns([0.12, 1.4])
        with logo_col:
            st.image(str(LOGO_PATH), width=72)
        with title_col:
            st.markdown("## WorkLens AI")
        return

    st.markdown("## WorkLens AI")


def render_role_badge(role: str) -> None:
    st.sidebar.markdown(
        f'<span class="wl-badge wl-badge-primary">{ROLE_LABELS[role]}</span>',
        unsafe_allow_html=True,
    )


def render_sidebar(role: str) -> None:
    user = SessionManager.get_user() or {}
    nav_items = list(ROUTES[role])
    current_page = current_page_for(role)

    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=150)
    else:
        st.sidebar.markdown("### WorkLens AI")

    st.sidebar.caption("Engineering visibility")
    render_role_badge(role)
    st.sidebar.divider()
    st.sidebar.caption("Navigation")

    selected_page = st.sidebar.radio(
        "Navigation",
        nav_items,
        index=nav_items.index(current_page),
        key=f"sidebar_nav_{role}",
        label_visibility="collapsed",
    )
    if selected_page != current_page:
        SessionManager.set_page(selected_page)
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown(f"**{user.get('name', 'User')}**")
    st.sidebar.caption(user.get("designation", "Team Member"))

    if st.sidebar.button("Logout", width="stretch", key="logout_btn"):
        SessionManager.logout()
        st.rerun()


def render_route(role: str) -> None:
    page = current_page_for(role)
    handler = ROUTES[role][page]

    try:
        handler()
    except Exception as exc:
        st.error("This page could not be loaded.")
        st.caption(str(exc))


def render_authenticated_app() -> None:
    role = normalize_role(SessionManager.get_role())
    if not role:
        st.error("Your session has an invalid role. Please sign in again.")
        if st.button("Return to login", type="primary"):
            SessionManager.logout()
            st.rerun()
        return

    render_sidebar(role)
    render_route(role)


def main() -> None:
    st.set_page_config(
        page_title="WorkLens AI - Engineering Visibility",
        page_icon=":material/analytics:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    SessionManager.initialize()
    load_theme()

    if not SessionManager.is_authenticated():
        hide_streamlit_sidebar()
        render_logo_header()
        show_login()
        return

    render_logo_header()
    render_authenticated_app()


if __name__ == "__main__":
    main()
