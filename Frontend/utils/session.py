"""
=========================================================
WorkLens AI
Session Manager
---------------------------------------------------------
Responsibilities

- Initialize session
- Login state
- Logout state
- User information
- Navigation
- Chat history
- Theme

No page should directly modify st.session_state.
=========================================================
"""

from __future__ import annotations

import streamlit as st


class SessionManager:
    """
    Centralized Session State Manager.
    """

    DEFAULTS = {

        # Authentication
        "authenticated": False,
        "user": None,
        "user_role": None,


        # Tokens (future backend)
        "access_token": None,
        "refresh_token": None,

        # Navigation
        "current_page": "Dashboard",

        # Theme
        "theme": "Light",

        # Notifications
        "notifications": 5,

        # AI Chat
        "chat_history": [],

        # Daily Update
        "submitted_update": None,

    }

    # -------------------------------------------------

    @classmethod
    def initialize(cls):

        """
        Initialize default values.
        """

        for key, value in cls.DEFAULTS.items():

            if key not in st.session_state:

                st.session_state[key] = value

    # -------------------------------------------------

    @classmethod
    def login(cls, user: dict, access_token: str | None = None, refresh_token: str | None = None):

        """
        Store user information.

        """

        st.session_state.authenticated = True

        st.session_state.user = user

        st.session_state.user_role = user["role"]

        st.session_state.access_token = access_token

        st.session_state.refresh_token = refresh_token

    # -------------------------------------------------

    @classmethod
    def logout(cls):

        """
        Clear user session.
        """

        for key in cls.DEFAULTS:

            st.session_state[key] = cls.DEFAULTS[key]

    # -------------------------------------------------

    @classmethod
    def is_authenticated(cls):

        return st.session_state.authenticated

    # -------------------------------------------------

    @classmethod
    def get_user(cls):

        return st.session_state.user

    # -------------------------------------------------

    @classmethod
    def get_role(cls):

        return st.session_state.user_role

    # -------------------------------------------------

    @classmethod
    def get_page(cls):

        return st.session_state.current_page

    # -------------------------------------------------

    @classmethod
    def set_page(cls, page: str):

        st.session_state.current_page = page

    # -------------------------------------------------

    @classmethod
    def get_theme(cls):

        return st.session_state.theme

    # -------------------------------------------------

    @classmethod
    def set_theme(cls, theme: str):

        st.session_state.theme = theme

    # -------------------------------------------------

    @classmethod
    def notifications(cls):

        return st.session_state.notifications

    # -------------------------------------------------

    @classmethod
    def set_notifications(cls, value: int):

        st.session_state.notifications = value

    # -------------------------------------------------

    @classmethod
    def add_chat(cls, role: str, message: str):

        st.session_state.chat_history.append(

            {
                "role": role,
                "message": message,
            }

        )

    # -------------------------------------------------

    @classmethod
    def get_chat(cls):

        return st.session_state.chat_history

    # -------------------------------------------------

    @classmethod
    def clear_chat(cls):

        st.session_state.chat_history = []

    # -------------------------------------------------

    @classmethod
    def save_daily_update(cls, data: dict):

        st.session_state.submitted_update = data

    # -------------------------------------------------

    @classmethod
    def get_daily_update(cls):

        return st.session_state.submitted_update


def initialize_session() -> None:
    SessionManager.initialize()


def is_authenticated() -> bool:
    return SessionManager.is_authenticated()


def get_user_role() -> str | None:
    return SessionManager.get_role()


def get_user() -> dict | None:
    return SessionManager.get_user()
