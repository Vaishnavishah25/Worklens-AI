from __future__ import annotations

import time

import streamlit as st

from services.auth_services import AuthService
from theme.theme import footer_note
import os
SHOW_DEMO = os.getenv("DEMO_MODE","false").lower() == True

DEMO_ACCOUNTS = {
    "Manager": {
        "email": "manager@worklens.ai",
        "password": "manager123",
        "icon": "Manager",
    },
    "Mentor": {
        "email": "mentor@worklens.ai",
        "password": "mentor123",
        "icon": "Mentor",
    },
    "Employee": {
        "email": "employee@worklens.ai",
        "password": "employee123",
        "icon": "Employee",
    },
}


def _feature_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="wl-login-feature">
            <div class="wl-login-feature-title">{title}</div>
            <div class="wl-login-feature-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="wl-login-hero-card">
            <div class="wl-login-kicker">Enterprise engineering intelligence</div>
            <div class="wl-login-hero-title">WorkLens AI</div>
            <div class="wl-login-hero-subtitle">Engineering Visibility Powered by AI</div>
            <div class="wl-login-hero-copy">
                Help engineering teams stay aligned with daily updates, blocker detection,
                mentor guidance, and delivery insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="wl-login-section-title">Why WorkLens?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        _feature_card("Daily Updates", "Track engineering work without interrupting developers.")
        _feature_card("AI Risk Detection", "Detect delivery risks before they become blockers.")
    with c2:
        _feature_card("Knowledge Continuity", "Preserve engineering knowledge across projects.")
        _feature_card("Team Health", "Measure confidence, blockers, and productivity.")


def render_demo_accounts() -> dict | None:
    st.markdown("### Demo Accounts")
    cols = st.columns(3)
    selected = None

    for index, (role, account) in enumerate(DEMO_ACCOUNTS.items()):
        with cols[index]:
            if st.button(account["icon"], use_container_width=True, key=f"demo_{role}"):
                selected = account
            st.caption(account["email"])

    return selected


def show_login() -> None:
    st.session_state.setdefault("login_email", "")
    st.session_state.setdefault("login_password", "")

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        render_hero()

    with right:
        st.markdown(
            """
            <div class="wl-login-welcome">
                <div class="wl-login-kicker">Secure workspace</div>
                <div class="wl-login-card-title">Welcome Back</div>
                <div class="wl-login-card-copy">Sign in to continue using WorkLens AI.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected = render_demo_accounts()
        if selected:
            st.session_state.login_email = selected["email"]
            st.session_state.login_password = selected["password"]
            st.session_state.email_input = selected["email"]
            st.session_state.password_input = selected["password"]
            st.rerun()

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                value=st.session_state.login_email,
                placeholder="manager@worklens.ai",
                key="email_input",
            )
            password = st.text_input(
                "Password",
                value=st.session_state.login_password,
                type="password",
                key="password_input",
            )
            submitted = st.form_submit_button(
                "Sign in to WorkLens",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not email.strip():
                st.error("Please enter your email.")
                st.stop()
            if not password.strip():
                st.error("Please enter your password.")
                st.stop()

            with st.spinner("Signing you in..."):
                time.sleep(0.3)
                success, message = AuthService.login(email=email.strip(), password=password)

            if success:
                st.success("Login successful. Redirecting...")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error(message)

        st.markdown(
            """
            <div class="wl-login-enterprise">
                <div class="wl-login-feature-title">Enterprise Ready</div>
                <div class="wl-login-feature-body">JWT Authentication - FastAPI - PostgreSQL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        footer_note("Version 1.0.0", "Built for Engineering Teams", divider_above=True)
