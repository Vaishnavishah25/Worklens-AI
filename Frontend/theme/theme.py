from __future__ import annotations

from pathlib import Path

import streamlit as st


COLORS = {
    "primary": "#6366f1",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#06b6d4",
}

SPACING = {
    "xs": "0.5rem",
    "sm": "0.75rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
}


def load_theme() -> None:
    """Load CSS only. UI helpers below intentionally use native Streamlit."""
    css_path = Path(__file__).parent / "styles.css"
    if not css_path.exists():
        st.warning(f"CSS file not found: {css_path}")
        return
    with open(css_path, encoding="utf-8") as fh:
        st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)


def badge(text: str, level: str = "info", icon: str | None = None) -> str:
    label = f"{icon} {text}" if icon else text
    return str(label)


def status_indicator(status: str, text: str = "", size: str = "sm") -> str:
    return text or status.title()


def hero_card(
    title: str,
    subtitle: str = "",
    eyebrow: str | None = None,
    badge_html: str | None = None,
) -> None:
    with st.container(border=True):
        if eyebrow:
            st.caption(eyebrow)
        left, right = st.columns([1, 0.25])
        with left:
            st.subheader(title)
            if subtitle:
                st.caption(subtitle)
        with right:
            if badge_html:
                st.info(badge_html)


def standard_card(
    title: str,
    body: str,
    eyebrow: str | None = None,
    badge_html: str | None = None,
    premium: bool = False,
    hover: bool = False,
):
    with st.container(border=True):
        if eyebrow:
            st.caption(eyebrow)
        if badge_html:
            left, right = st.columns([1, 0.35])
            with left:
                st.markdown(f"**{title}**")
            with right:
                st.caption(badge_html)
        else:
            st.markdown(f"**{title}**")
        if body:
            st.write(str(body))


def panel_card(title: str, content: str, compact: bool = False) -> None:
    standard_card(title, content)


def card(
    title: str,
    body: str,
    eyebrow: str | None = None,
    badge_html: str | None = None,
    premium: bool = False,
    hover: bool = False,
) -> None:
    standard_card(title, body, eyebrow=eyebrow, badge_html=badge_html, premium=premium, hover=hover)


def section_header(title: str, subtitle: str = "", action_html: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    if action_html:
        st.info(action_html)
    st.divider()


def metric_card(
    title: str,
    value: str,
    delta: str = "",
    color: str = "primary",
    icon: str | None = None,
) -> None:
    label = f"{icon} {title}" if icon else title
    st.metric(label, value, delta if delta else None)


def spacer(size: str = "md") -> None:
    st.write("")


def divider(size: str = "lg") -> None:
    st.divider()


def two_columns(gap: str = "lg") -> tuple:
    gap_map = {"sm": "small", "md": "medium", "lg": "large"}
    return st.columns([1, 1], gap=gap_map.get(gap, "large"))


def three_columns(gap: str = "lg") -> tuple:
    gap_map = {"sm": "small", "md": "medium", "lg": "large"}
    return st.columns([1, 1, 1], gap=gap_map.get(gap, "large"))


def four_columns(gap: str = "lg") -> tuple:
    gap_map = {"sm": "small", "md": "medium", "lg": "large"}
    return st.columns([1, 1, 1, 1], gap=gap_map.get(gap, "large"))


def empty_state(title: str, description: str, icon: str = "") -> None:
    with st.container(border=True):
        if icon:
            st.caption(icon)
        st.subheader(title)
        st.caption(description)


def loading(message: str = "Loading...") -> None:
    with st.spinner(message):
        pass


def alert(message: str, alert_type: str = "info", icon: str | None = None) -> None:
    text = f"{icon} {message}" if icon else message
    if alert_type == "success":
        st.success(text)
    elif alert_type == "warning":
        st.warning(text)
    elif alert_type in {"danger", "error"}:
        st.error(text)
    else:
        st.info(text)


def timeline_item(label: str, content: str, status: str = "completed") -> dict:
    return {"label": label, "content": content, "status": status}


def render_timeline(items: list[dict]) -> None:
    for item in items:
        with st.container(border=True):
            st.markdown(f"**{item.get('label', '')}**")
            st.caption(item.get("content", ""))
            st.caption(item.get("status", "completed").replace("-", " ").title())


def footer_note(*lines: str, divider_above: bool = True) -> None:
    if divider_above:
        st.divider()
    for line in lines:
        st.caption(line)


def render_grid(items: list[str], columns: int = 4) -> None:
    cols = st.columns(max(1, min(columns, 6)))
    for index, item in enumerate(items):
        with cols[index % len(cols)]:
            st.write(item)
