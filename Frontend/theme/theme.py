from __future__ import annotations

from pathlib import Path

import streamlit as st


COLORS = {
    "primary": "#2563eb",
    "success": "#059669",
    "warning": "#d97706",
    "danger": "#dc2626",
    "info": "#0891b2",
    "muted": "#64748b",
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
    level = (level or "info").lower()
    return f'<span class="wl-badge wl-badge-{level}">{label}</span>'


def status_indicator(status: str, text: str = "", size: str = "sm") -> str:
    label = text or status.title()
    status_class = (status or "info").lower().replace(" ", "-")
    return f'<span class="wl-status wl-status-{status_class}">{label}</span>'


def _render_badge(badge_html: str | None) -> None:
    if badge_html:
        st.markdown(badge_html, unsafe_allow_html=True)


def hero_card(
    title: str,
    subtitle: str = "",
    eyebrow: str | None = None,
    badge_html: str | None = None,
) -> None:
    with st.container(border=True):
        if eyebrow:
            st.markdown(f'<div class="wl-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
        left, right = st.columns([1, 0.25])
        with left:
            st.subheader(title)
            if subtitle:
                st.caption(subtitle)
        with right:
            _render_badge(badge_html)


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
            st.markdown(f'<div class="wl-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
        if badge_html:
            left, right = st.columns([1, 0.35])
            with left:
                st.markdown(f"**{title}**")
            with right:
                _render_badge(badge_html)
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
    st.markdown(f'<div class="wl-page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="wl-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    if action_html:
        st.markdown(action_html, unsafe_allow_html=True)
    st.markdown('<div class="wl-section-rule"></div>', unsafe_allow_html=True)


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
    sizes = {"xs": "0.25rem", "sm": "0.5rem", "md": "0.85rem", "lg": "1.25rem", "xl": "1.75rem"}
    st.markdown(f'<div style="height:{sizes.get(size, "0.85rem")}"></div>', unsafe_allow_html=True)


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
            st.markdown(f'<div class="wl-empty-icon">{icon}</div>', unsafe_allow_html=True)
        st.markdown(f"**{title}**")
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
            st.markdown(
                status_indicator(item.get("status", "completed"), item.get("status", "completed").replace("-", " ").title()),
                unsafe_allow_html=True,
            )
            st.markdown(f"**{item.get('label', '')}**")
            st.caption(item.get("content", ""))


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


def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, Arial, sans-serif", color="#0f172a"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=18, b=18),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0", tickfont=dict(color="#64748b"))
    fig.update_yaxes(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0", tickfont=dict(color="#64748b"))
    return fig
