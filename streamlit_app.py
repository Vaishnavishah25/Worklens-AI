from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="WorkLens AI",
    page_icon="WL",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("WORKLENS_API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_TEAM_ID = "550e8400-e29b-41d4-a716-446655440000"


# ── Live data fetchers (replace hardcoded DataFrames) ──

@st.cache_data(ttl=15)
def fetch_team_dashboard() -> list[dict]:
    """Fetch live team dashboard data from the backend."""
    try:
        return _request_json(f"{API_BASE_URL}/api/v1/auth/team-dashboard", timeout=10)
    except Exception:
        return []


@st.cache_data(ttl=15)
def fetch_blockers(status_filter: str | None = None) -> list[dict]:
    """Fetch live blockers from the backend."""
    try:
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        return _request_json(f"{API_BASE_URL}/api/v1/auth/blockers", params=params, timeout=10)
    except Exception:
        return []


@st.cache_data(ttl=15)
def fetch_employees() -> list[dict]:
    """Fetch live employee list from the backend."""
    try:
        return _request_json(f"{API_BASE_URL}/api/v1/auth/employees", timeout=10)
    except Exception:
        return []


def _format_last_update(iso_str: str | None) -> str:
    """Convert ISO datetime to a human-friendly 'X ago' string."""
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = datetime.utcnow() - dt
        if delta.days == 0:
            if delta.seconds < 3600:
                return f"{delta.seconds // 60}m ago"
            return f"{delta.seconds // 3600}h ago"
        elif delta.days == 1:
            return "Yesterday"
        return f"{delta.days}d ago"
    except Exception:
        return iso_str
def fetch_feedback(user_id: int) -> list[dict]:
    try:
        return _request_json(f"{API_BASE_URL}/api/v1/auth/feedback", params={"user_id": user_id}, timeout=10)
    except Exception:
        return []

def team_dashboard_as_dataframe() -> pd.DataFrame:
    rows = fetch_team_dashboard()
    if not rows:
        return pd.DataFrame(columns=["Employee", "Role", "Last Update", "Avg Confidence", "Open Blockers", "Total Updates"])
    return pd.DataFrame([
        {
            "Employee": r["name"],
            "Role": r.get("title") or r["role"],
            "Last Update": _format_last_update(r.get("last_update")),
            "Avg Confidence": r.get("avg_confidence"),
            "Open Blockers": r.get("open_blockers", 0),
            "Total Updates": r.get("total_updates", 0),
        }
        for r in rows
    ])


def blockers_as_dataframe() -> pd.DataFrame:
    rows = fetch_blockers()
    if not rows:
        return pd.DataFrame(columns=["Employee", "Blocker", "Severity", "Age", "Status"])
    today = date.today()
    def _age(created_at: str | None) -> str:
        if not created_at:
            return "?"
        try:
            dt = datetime.fromisoformat(created_at).date()
            d = (today - dt).days
            if d == 0:
                return "Today"
            elif d == 1:
                return "1d"
            return f"{d}d"
        except Exception:
            return "?"
    return pd.DataFrame([
        {
            "Employee": r.get("employee_name") or f"User {r['user_id']}",
            "Blocker": r["description"],
            "Severity": r["severity"],
            "Age": _age(r.get("created_at")),
            "Status": r["status"].capitalize(),
        }
        for r in rows
    ])


TASKS = pd.DataFrame(
    [
        {"Task": "Finalize billing API adapter", "Due": "Today", "Status": "In Progress", "Risk": "Medium"},
        {"Task": "Add retry telemetry for webhook worker", "Due": "Yesterday", "Status": "Overdue", "Risk": "High"},
        {"Task": "Document subscription state machine", "Due": "Jun 27", "Status": "In Progress", "Risk": "Low"},
        {"Task": "Patch invoice export regression", "Due": "Jun 23", "Status": "Completed", "Risk": "Low"},
    ]
)


FEEDBACK = pd.DataFrame(
    [
        {
            "Type": "Guidance",
            "From": "Ravi Mehta",
            "Date": "Today",
            "Message": "Good progress on the adapter. Please call out billing API churn early in tomorrow's update.",
            "Unread": True,
        },
        {
            "Type": "Praise",
            "From": "Maya Chen",
            "Date": "Yesterday",
            "Message": "Strong ownership on debugging the invoice export issue under time pressure.",
            "Unread": False,
        },
        {
            "Type": "Concern",
            "From": "Ravi Mehta",
            "Date": "Monday",
            "Message": "Confidence dipped while the dependency stayed open. Let's narrow the next step to one unblock request.",
            "Unread": False,
        },
    ]
)
 
 
def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --wl-bg: #f7f8fa;
            --wl-surface: #ffffff;
            --wl-surface-2: #f3f4f6;
            --wl-border: #e5e7eb;
            --wl-text: #111827;
            --wl-muted: #6b7280;
            --wl-primary: #2563eb;
            --wl-ai: #7c3aed;
            --wl-teal: #14b8a6;
            --wl-good: #16a34a;
            --wl-warn: #f59e0b;
            --wl-bad: #dc2626;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: var(--wl-bg);
            color: var(--wl-text);
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] * { color: #f9fafb; }
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            justify-content: flex-start;
            border: 0;
            border-radius: 8px;
            color: #e5e7eb;
            background: transparent;
            padding: .62rem .75rem;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255,255,255,.08);
            color: #ffffff;
        }
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }
        h1, h2, h3 { letter-spacing: 0; }
        h1 { font-size: 1.7rem; line-height: 2.1rem; font-weight: 700; }
        h2 { font-size: 1.2rem; font-weight: 650; }
        h3 { font-size: 1rem; font-weight: 650; }
        div[data-testid="stMetric"] {
            background: var(--wl-surface);
            border: 1px solid var(--wl-border);
            border-radius: 8px;
            padding: 18px 18px 14px;
            box-shadow: 0 1px 1px rgba(17,24,39,.03);
        }
        div[data-testid="stMetric"] label p {
            color: var(--wl-muted);
            font-size: .78rem;
        }
        .wl-card {
            background: var(--wl-surface);
            border: 1px solid var(--wl-border);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 1px 2px rgba(17,24,39,.04);
            min-height: 100%;
        }
        .wl-tight { padding: 14px; }
        .wl-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }
        .wl-muted { color: var(--wl-muted); font-size: .88rem; }
        .wl-eyebrow {
            color: var(--wl-muted);
            font-size: .72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: .35rem;
        }
        .wl-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: .74rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .risk-low { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
        .risk-medium { color: #92400e; background: #fef3c7; border-color: #fde68a; }
        .risk-high { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .type-ai { color: #5b21b6; background: #ede9fe; border-color: #ddd6fe; }
        .type-info { color: #075985; background: #e0f2fe; border-color: #bae6fd; }
        .type-teal { color: #115e59; background: #ccfbf1; border-color: #99f6e4; }
        .wl-divider { height: 1px; background: var(--wl-border); margin: 14px 0; }
        .wl-table-note {
            color: var(--wl-muted);
            font-size: .8rem;
            margin-top: -8px;
            margin-bottom: 8px;
        }
        .wl-chat {
            background: #ffffff;
            border: 1px solid var(--wl-border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .wl-ai-response {
            border-left: 3px solid var(--wl-ai);
            background: #faf7ff;
        }
        .stButton > button {
            border-radius: 8px;
            border: 1px solid var(--wl-border);
            min-height: 38px;
            font-weight: 650;
        }
        .stButton > button[kind="primary"] {
            background: var(--wl-primary);
            border-color: var(--wl-primary);
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            border-radius: 8px;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--wl-border);
            border-radius: 8px;
            overflow: hidden;
        }
        @media (max-width: 760px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .wl-row { align-items: flex-start; flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
 
 
def initialize_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("page", "Dashboard")
    st.session_state.setdefault("theme", "Light")
    st.session_state.setdefault("notifications", 5)
    st.session_state.setdefault("submitted_update", None)
    st.session_state.setdefault("ai_messages", [])
    st.session_state.setdefault("weekly_summary_answer", None)
    st.session_state.setdefault("ai_recommendation_answer", None)


def _request_json(url: str, params: dict | None = None, timeout: int = 30):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _post_json(url: str, payload: dict, timeout: int = 30):
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_ai_answer(question: str, team_id: str = DEFAULT_TEAM_ID) -> str:
    try:
        data = _request_json(
            f"{API_BASE_URL}/api/v1/ai/query/sync",
            params={"question": question, "team_id": team_id},
            timeout=45,
        )
    except Exception as exc:
        return f"Backend AI request failed: {exc}"
    return data.get("answer") or "No AI answer was returned."


def create_user_account(name: str, email: str, password: str, role: str, title: str | None = None) -> tuple[bool, str]:
    try:
        user = _post_json(
            f"{API_BASE_URL}/api/v1/auth/users",
            {
                "name": name.strip(),
                "email": email.strip().lower(),
                "password": password,
                "role": role,
                "title": title or role,
            },
            timeout=15,
        )
    except Exception as exc:
        return False, f"Could not create user: {exc}"
    return True, f"Created {user['email']} in the local database."
 
 
def badge(label: str, kind: str = "info") -> str:
    return f'<span class="wl-badge {kind}">{label}</span>'
 
 
def card(title: str, body: str, eyebrow: str | None = None, badge_html: str | None = None) -> None:
    eyebrow_html = f'<div class="wl-eyebrow">{eyebrow}</div>' if eyebrow else ""
    badge_part = badge_html or ""
    st.markdown(
        f"""
        <div class="wl-card">
            <div class="wl-row">
                <div>
                    {eyebrow_html}
                    <h3 style="margin:.05rem 0 .35rem">{title}</h3>
                </div>
                <div>{badge_part}</div>
            </div>
            <div class="wl-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def login_screen() -> None:
    inject_css()
    left, right = st.columns([1.08, 1], gap="large")
    with left:
        st.markdown(
            """
            <div style="min-height: calc(100vh - 80px); background:#111827; border-radius:12px; padding:42px; color:#fff; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="font-size:.82rem; font-weight:800; color:#93c5fd; letter-spacing:.08em; text-transform:uppercase;">WorkLens AI</div>
                    <h1 style="font-size:2.6rem; line-height:3rem; margin:18px 0 14px; color:#fff;">Engineering intelligence for modern teams.</h1>
                    <p style="font-size:1.05rem; line-height:1.75rem; color:#cbd5e1; max-width:620px;">
                        Surface blockers, detect delivery risk, and help every engineer get the support they need before sprint health declines.
                    </p>
                </div>
                <div style="display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;">
                    <div class="wl-card wl-tight" style="background:#1f2937;border-color:#374151;color:#fff;"><b>Risk insights</b><br><span style="color:#cbd5e1;">Explainable signals</span></div>
                    <div class="wl-card wl-tight" style="background:#1f2937;border-color:#374151;color:#fff;"><b>Daily updates</b><br><span style="color:#cbd5e1;">Two-minute flow</span></div>
                    <div class="wl-card wl-tight" style="background:#1f2937;border-color:#374151;color:#fff;"><b>Mentor feedback</b><br><span style="color:#cbd5e1;">Guided growth</span></div>
                    <div class="wl-card wl-tight" style="background:#1f2937;border-color:#374151;color:#fff;"><b>AI assistant</b><br><span style="color:#cbd5e1;">Cited recommendations</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("## Sign in")
        st.caption("Use your WorkLens credentials or one of the demo accounts.")
        with st.form("login_form"):
            email = st.text_input("Email / Username", placeholder="manager@worklens.ai")
            password = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me", value=True)
            submitted = st.form_submit_button("Log in", use_container_width=True, type="primary")
        with st.expander("Default accounts", expanded=True):
            st.code(
                "Manager  manager@worklens.ai / manager123\n"
                "Mentor   mentor@worklens.ai / mentor123\n"
                "Employee employee@worklens.ai / employee123",
                language="text",
            )
        with st.expander("Create account", expanded=False):
            with st.form("create_user_form"):
                new_name = st.text_input("Full name", placeholder="New User")
                new_email = st.text_input("New email", placeholder="new.user@worklens.ai")
                new_password = st.text_input("New password", type="password")
                new_role = st.selectbox("Role", ["Employee", "Mentor", "Manager"])
                new_title = st.text_input("Title", placeholder="Software Engineer")
                create_submitted = st.form_submit_button("Store user in database", use_container_width=True)
            if create_submitted:
                if not new_name.strip() or not new_email.strip() or len(new_password) < 6:
                    st.error("Enter a name, email, and password with at least 6 characters.")
                else:
                    ok, message = create_user_account(new_name, new_email, new_password, new_role, new_title)
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/auth/login",
                    json={"email": email.strip().lower(), "password": password},
                    timeout=10,
                )
            except Exception:
                st.error("Unable to reach the backend authentication service.")
                return
            if response.ok:
                user = response.json()
                st.session_state.authenticated = True
                st.session_state.user = {**user, "remember": remember}
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password.")
 
 
def sidebar() -> None:
    user = st.session_state.user
    nav = {
        "Employee": ["Dashboard", "Daily Update", "My Tasks", "Progress Timeline", "Feedback Inbox", "My Risk"],
        "Mentor": ["Dashboard", "Mentees", "Feedback Composer", "Feedback History"],
        "Manager": ["Dashboard", "Team Risk", "Blockers", "AI Assistant", "Weekly Summary", "Analytics", "Alerts"],
    }[user["role"]]
    st.sidebar.markdown("### WorkLens AI")
    st.sidebar.caption("Engineering Org")
    st.sidebar.markdown(badge(user["role"], "type-ai" if user["role"] == "Manager" else "type-teal"), unsafe_allow_html=True)
    st.sidebar.divider()
    for item in nav:
        if st.sidebar.button(item, key=f"nav_{item}", use_container_width=True):
            st.session_state.page = item
    st.sidebar.divider()
    st.sidebar.caption(f"{user['name']} · {user['title']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.page = "Dashboard"
        st.rerun()
 
 
def top_bar(title: str, subtitle: str | None = None) -> None:
    left, mid, right = st.columns([1.7, 1.2, 1])
    with left:
        st.markdown(f"# {title}")
        if subtitle:
            st.caption(subtitle)
    with mid:
        st.text_input("Search", placeholder="Search employees, blockers, updates...", label_visibility="collapsed")
    with right:
        c1, c2, c3 = st.columns([1, 1, 1])
        c1.selectbox("Team", ["Platform", "Product Eng", "Data"], label_visibility="collapsed")
        st.session_state.theme = c2.selectbox("Theme", ["Light", "Dark"], label_visibility="collapsed")
        c3.metric("Alerts", st.session_state.notifications, delta="2 critical")
    st.divider()
 
 
def risk_kind(risk: str) -> str:
    return {"Low": "risk-low", "Medium": "risk-medium", "High": "risk-high"}.get(risk, "type-info")
 
 
def employee_dashboard() -> None:
    top_bar("Employee Dashboard", "Submit updates, track blockers, and understand your progress signals.")
    col1, col2 = st.columns([1.35, 1])
    with col1:
        st.markdown(
            f"""
            <div class="wl-card">
                <div class="wl-eyebrow">Today</div>
                <h2 style="margin:.1rem 0 .35rem;">Good morning, {st.session_state.user['name'].split()[0]}.</h2>
                <div class="wl-muted">Ready to share today’s progress? The update flow is optimized for two minutes.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("Submit daily update", type="primary", use_container_width=True):
            st.session_state.page = "Daily Update"
            st.rerun()
        if st.button("View last update", use_container_width=True):
            if st.session_state.submitted_update:
                st.json(st.session_state.submitted_update)
            else:
                st.info("No update has been submitted in this session yet.")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Daily streak", "8 days", "+2")
    k2.metric("Confidence trend", "3.6 / 5", "-0.4")
    k3.metric("Current risk", "42", "Medium")
    k4.metric("Active blockers", "1", "API contract")
    k5.metric("Feedback received", "3", "1 unread")
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Progress timeline")
        timeline()
    with right:
        st.subheader("Recent feedback")
        feedback_list()
        st.subheader("Personal risk")
        personal_risk_widget()
        left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Progress timeline")
        timeline()
    with right:
        st.subheader("Recent feedback")
        feedback_list()
        st.subheader("Personal risk")
        personal_risk_widget()
 
 
def daily_update() -> None:
    top_bar("Daily Update", "Capture work done, blockers, next steps, and confidence.")
    with st.form("daily_update_form"):
        work_done = st.text_area("Work Done", placeholder="What did you complete or make progress on today?", height=130)
        no_blockers = st.checkbox("No blockers today")
        blocker = st.text_area("Blockers", placeholder="What is blocking or slowing you down?", height=100, disabled=no_blockers)
        severity = st.segmented_control("Severity", ["None", "Low", "Medium", "High", "Critical"], default="None")
        next_steps = st.text_area("Next Steps", placeholder="What are you planning to do next?", height=100)
        confidence = st.slider("Confidence", min_value=1, max_value=5, value=4)
        submitted = st.form_submit_button("Submit update", type="primary", use_container_width=True)
    if submitted:
        if not work_done or not next_steps:
            st.error("Please complete Work Done and Next Steps before submitting.")
        elif severity != "None" and not no_blockers and not blocker:
            st.error("Please describe the blocker or select 'No blockers today'.")
        else:
            payload = {
                "user_id": st.session_state.user["id"],
                "work_done": work_done,
                "planned_work": next_steps,
                "confidence_score": float(confidence),
                "blocker_description": None if no_blockers else blocker,
                "blocker_severity": None if severity == "None" else severity,
            }
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/auth/daily-updates",
                    json=payload,
                    timeout=10,
                )
            except Exception as exc:
                st.error(f"Unable to reach the backend service: {exc}")
                return

            if response.ok:
                st.session_state.submitted_update = {
                    **payload,
                    "submitted_at": datetime.now().strftime("%I:%M %p"),
                }
                st.success("Update submitted and stored in the database.")
            else:
                st.error(f"Submission failed: {response.text}")
    if st.session_state.submitted_update:
        with st.expander("Submitted update", expanded=True):
            st.json(st.session_state.submitted_update)
 
 
def my_tasks() -> None:
    top_bar("My Tasks", "Review overdue, in-progress, and completed work.")
    overdue, in_progress, completed = st.tabs(["Overdue", "In Progress", "Completed"])
    for tab, status in [(overdue, "Overdue"), (in_progress, "In Progress"), (completed, "Completed")]:
        with tab:
            rows = TASKS[TASKS["Status"] == status]
            if rows.empty:
                st.info(f"No {status.lower()} tasks.")
            for _, row in rows.iterrows():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"**{row['Task']}**  \n<span class='wl-muted'>Due {row['Due']}</span>", unsafe_allow_html=True)
                c2.markdown(badge(row["Risk"], risk_kind(row["Risk"])), unsafe_allow_html=True)
                if status != "Completed":
                    if c3.button("Mark done", key=f"done_{row['Task']}"):
                        st.success(f"Marked '{row['Task']}' as done for this session.")
                    if c3.button("Report blocker", key=f"blocker_{row['Task']}"):
                        st.warning(f"Blocker report started for '{row['Task']}'.")
 
 
def timeline() -> None:
    events = [
        ("Today", "Daily update submitted", "Confidence 3.6 · Billing adapter in progress"),
        ("Yesterday", "Blocker opened", "API contract still changing for billing service"),
        ("Monday", "Feedback received", "Guidance from Ravi on narrowing unblock requests"),
        ("Last Friday", "Blocker resolved", "Invoice export regression patched"),
    ]
    for when, title, details in events:
        st.markdown(
            f"""
            <div class="wl-card wl-tight" style="margin-bottom:10px;">
                <div class="wl-row">
                    <b>{title}</b><span class="wl-muted">{when}</span>
                </div>
                <div class="wl-muted">{details}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
 
def feedback_list(user_id: int | None = None) -> None:
    user_id = user_id or st.session_state.user["id"]
    rows = fetch_feedback(user_id)
    if not rows:
        st.info("No feedback received yet.")
        return
    kind_map = {"praise": "risk-low", "guidance": "type-info", "concern": "risk-medium"}
    for r in rows:
        kind = kind_map.get(r["type"], "type-info")
        unread = " · unread" if not r["is_read"] else ""
        when = r["created_at"][:10] if r.get("created_at") else ""
        st.markdown(
            f"""
            <div class="wl-card wl-tight" style="margin-bottom:10px;">
                <div class="wl-row">
                    <b>{r['from_name']}</b>{badge(r['type'].capitalize(), kind)}
                </div>
                <div class="wl-muted">{when}{unread}</div>
                <div style="margin-top:8px;">{r['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
 
def personal_risk_widget() -> None:
    st.markdown(
        f"""
        <div class="wl-card">
            <div class="wl-row">
                <div><div class="wl-eyebrow">Risk Score</div><h2 style="margin:0;">42 / 100</h2></div>
                {badge("Medium", "risk-medium")}
            </div>
            <div class="wl-divider"></div>
            <div class="wl-muted">Contributing factors</div>
            <ul>
                <li>1 unresolved blocker</li>
                <li>Confidence declined over 3 days</li>
                <li>1 overdue task</li>
                <li>Daily updates completed consistently</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
        
    )
 
 
def progress_timeline_page() -> None:
    top_bar("Progress Timeline", "A chronological view of updates, confidence, blockers, and feedback.")
    timeline()
 
def feedback_inbox_page() -> None:
    top_bar("Feedback Inbox", "Review praise, guidance, and concerns from mentors and managers.")
    feedback_list()
 
 
def personal_risk_page() -> None:
    top_bar("My Risk", "Transparent, explainable risk scoring focused on support.")
    left, right = st.columns([.9, 1.1], gap="large")
    with left:
        personal_risk_widget()
        left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Progress timeline")
        timeline()
    with right:
        st.subheader("Recent feedback")
        feedback_list()
        st.subheader("Personal risk")
        personal_risk_widget()
        st.subheader("My blockers")
        my_blockers = fetch_blockers(user_id=st.session_state.user["id"])
        if not my_blockers:
            st.info("No blockers reported.")
        for b in my_blockers:
            st.markdown(
                f"**{b['description']}** — "
                f"{badge(b['status'].capitalize(), risk_kind({'open':'Medium','escalated':'High','resolved':'Low'}.get(b['status'],'Low')))}",
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Confidence trend")
        trend_chart()
 
 
def manager_dashboard() -> None:
    top_bar("Manager Dashboard", "Team health, blockers, AI recommendations, and risk signals.")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Team Health Score", "78", "+4")
    k2.metric("High Risk Members", "2", "+1")
    k3.metric("Open Blockers", "4", "1 critical")
    k4.metric("Update Completion", "91%", "+6%")
    k5.metric("Unread Alerts", "5", "+2")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.subheader("Team risk overview")
        team_risk_table()
        st.subheader("Active blockers")
        blockers_table()
    with right:
        weekly_summary_card()
        ai_recommendations()
 
 
def team_risk_table() -> None:
    display = team_dashboard_as_dataframe()
    if display.empty:
        st.info("No team data found. Have employees submitted daily updates?")
    else:
        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
        )
    st.caption("Actions: view profile, prepare 1:1, message mentor, ask AI, create action item.")


def blockers_table() -> None:
    display = blockers_as_dataframe()
    if display.empty:
        st.info("No blockers found in the database yet.")
    else:
        st.dataframe(display, hide_index=True, use_container_width=True)
    st.caption("Critical and aging blockers should be triaged first.")
 
 
def weekly_summary_card() -> None:
    summary = (
        st.session_state.weekly_summary_answer
        or "Click Generate weekly summary to create an AI summary from the seeded team data."
    ).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="wl-card">
            <div class="wl-row">
                <h3 style="margin:0;">Weekly Summary</h3>
                <span class="wl-badge type-ai">AI generated</span>
            </div>
            <div class="wl-divider"></div>
            <div>{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def ai_recommendations() -> None:
    answer = (
        st.session_state.ai_recommendation_answer
        or "Click Generate AI recommendation to ask WorkLens who needs attention."
    ).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="wl-card wl-ai-response">
            <div class="wl-eyebrow">AI WorkLens Assistant</div>
            <h3 style="margin:.1rem 0;">Who needs immediate help?</h3>
            <p>{answer}</p>
            <div class="wl-muted">Sources: daily updates, active blockers, risk scores</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    button_label = "Refresh AI recommendation" if st.session_state.ai_recommendation_answer else "Generate AI recommendation"
    if st.button(button_label, use_container_width=True):
        st.session_state.ai_recommendation_answer = get_ai_answer("Who needs immediate help and what should I do today?")
        st.rerun()
 
 
def team_risk_page() -> None:
    top_bar("Team Risk", "Interactive risk table with filters and row-level actions.")
    c1, c2, c3, c4 = st.columns(4)
    c1.selectbox("Risk level", ["All", "High", "Medium", "Low"])
    c2.selectbox("Update status", ["All", "Submitted", "Missing", "Late"])
    c3.selectbox("Blocker severity", ["All", "Critical", "High", "Medium", "Low"])
    c4.selectbox("Mentor", ["All", "Ravi Mehta", "Elena Torres"])
    team_risk_table()
 
 
def blockers_page() -> None:
    top_bar("Active Blockers", "Track severity, age, status, ownership, and escalation.")
    blockers_table()
    c1, c2, c3 = st.columns(3)
    if c1.button("Assign owner", use_container_width=True):
        st.success("Owner assignment simulated for the selected blocker.")
    if c2.button("Escalate selected", use_container_width=True):
        st.warning("Selected blocker escalation simulated.")
    if c3.button("Mark resolved", use_container_width=True):
        st.success("Selected blocker marked resolved for this session.")
 
 
def ai_assistant_page() -> None:
    top_bar("AI WorkLens Assistant", "Ask cited questions about delivery risk, blockers, and team health.")
    history, chat, sources = st.columns([.75, 1.6, .9], gap="large")
    with history:
        st.subheader("History")
        for item in ["Sprint risk review", "1:1 prep for Priya", "Weekly blocker summary"]:
            if st.button(item, use_container_width=True):
                prompt = {
                    "Sprint risk review": "Give me a sprint risk review for this team.",
                    "1:1 prep for Priya": "Prepare me for a 1 on 1 with Priya today.",
                    "Weekly blocker summary": "Summarize the open blockers for this team.",
                }[item]
                st.session_state.ai_messages.append(("user", prompt))
                st.session_state.ai_messages.append(("assistant", get_ai_answer(prompt)))
                st.rerun()
        st.subheader("Suggested prompts")
        for prompt in ["Who needs immediate help?", "What is blocking the sprint?", "Prepare my 1:1s.", "Why is Priya delayed?"]:
            if st.button(prompt, key=f"suggested_{prompt}", use_container_width=True):
                st.session_state.ai_messages.append(("user", prompt))
                st.session_state.ai_messages.append(("assistant", get_ai_answer(prompt)))
                st.rerun()
    with chat:
        if not st.session_state.ai_messages:
            st.info("Ask a question below, or click a suggested prompt on the left.")
        for role, message in st.session_state.ai_messages:
            css_class = "wl-chat wl-ai-response" if role == "assistant" else "wl-chat"
            label = "WorkLens AI" if role == "assistant" else "You"
            st.markdown(
                f'<div class="{css_class}"><b>{label}</b><br>{message.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
        prompt = st.chat_input("Ask about risks, blockers, updates, or 1:1 prep...")
        if prompt:
            st.session_state.ai_messages.append(("user", prompt))
            st.session_state.ai_messages.append(("assistant", get_ai_answer(prompt)))
            st.rerun()
    with sources:
        st.subheader("Sources")
        card("Daily updates", "Retrieved from FAISS seeded update records.", badge_html=badge("Cited", "type-ai"))
        card("Blockers", "Open blocker records are included in AI context.", badge_html=badge("Live", "risk-medium"))
        card("Team ID", DEFAULT_TEAM_ID, badge_html=badge("Active", "type-teal"))
 
 
def weekly_summary_page() -> None:
    top_bar("Weekly Summary", "AI-generated highlights, concerns, and recommendations.")
    weekly_summary_card()
    c1, c2, c3, c4 = st.columns(4)
    summary_button = "Regenerate" if st.session_state.weekly_summary_answer else "Generate"
    if c1.button(summary_button, use_container_width=True):
        st.session_state.weekly_summary_answer = get_ai_answer(
            "Regenerate the weekly team summary with highlights, concerns, and actions."
        )
        st.rerun()
    if c2.button("Copy", use_container_width=True):
        st.info("Summary is ready above for copying.")
    if c3.button("Export", use_container_width=True):
        st.download_button(
            "Download summary text",
            st.session_state.weekly_summary_answer or "",
            file_name="worklens_weekly_summary.txt",
            use_container_width=True,
        )
    if c4.button("Send to Slack", use_container_width=True):
        st.success("Slack send simulated. Connect a Slack webhook when ready.")
 
 
def analytics_page() -> None:
    top_bar("Analytics", "Team health trends, blockers, confidence, completion, and risk distribution.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("Team health trend")
        trend_chart()
    with c2:
        st.subheader("Risk distribution")
        risk_distribution_chart()
    c3, c4 = st.columns(2, gap="large")
    with c3:
        st.subheader("Blockers per week")
        blocker_chart()
    with c4:
        st.subheader("Update completion heatmap")
        heatmap_chart()
    st.subheader("Confidence radar")
    radar_chart()
def fetch_team_feedback(manager_id: int) -> list[dict]:
    try:
        return _request_json(f"{API_BASE_URL}/api/v1/auth/feedback/team", params={"manager_id": manager_id}, timeout=10)
    except Exception:
        return []


def alerts_page() -> None:
    top_bar("Alerts", "Prioritized notifications and risk events.")
    alerts = [
        ("Critical", "Noah's warehouse migration blocker is escalated and aging.", "risk-high"),
        ("Warning", "Anita's confidence has declined for three consecutive updates.", "risk-medium"),
        ("Info", "Weekly summary is ready for review.", "type-info"),
        ("Success", "Jordan resolved all assigned blockers.", "risk-low"),
    ]
    for level, message, kind in alerts:
        card(level, message, badge_html=badge(level, kind))

    st.subheader("Team feedback shared with you")
    rows = fetch_team_feedback(st.session_state.user["id"])
    if not rows:
        st.info("No feedback has been shared with 'Employee and manager' visibility yet.")
    kind_map = {"praise": "risk-low", "guidance": "type-info", "concern": "risk-medium"}
    for r in rows:
        when = r["created_at"][:10] if r.get("created_at") else ""
        card(
            f"{r['type'].capitalize()} for {r['to_name']}",
            r["content"],
            eyebrow=f"From {r['from_name']} · {when}",
            badge_html=badge(r["type"].capitalize(), kind_map.get(r["type"], "type-info")),
        )
 
def trend_chart() -> None:
    days = [date.today() - timedelta(days=i) for i in range(13, -1, -1)]
    values = [72, 73, 71, 69, 70, 74, 76, 78, 77, 75, 76, 78, 79, 78]
    fig = px.line(x=days, y=values, markers=True, labels={"x": "Date", "y": "Score"})
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
 
 
def risk_distribution_chart() -> None:
    fig = px.pie(names=["Low", "Medium", "High"], values=[2, 1, 2], hole=.58, color=["Low", "Medium", "High"], color_discrete_map={"Low": "#16a34a", "Medium": "#f59e0b", "High": "#dc2626"})
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8))
    st.plotly_chart(fig, use_container_width=True)
 
 
def blocker_chart() -> None:
    data = pd.DataFrame({"Week": ["W1", "W2", "W3", "W4"], "Low": [2, 1, 3, 1], "Medium": [3, 4, 2, 3], "High": [1, 2, 2, 3], "Critical": [0, 1, 0, 1]})
    fig = px.bar(data, x="Week", y=["Low", "Medium", "High", "Critical"], barmode="stack")
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
 
 
def heatmap_chart() -> None:
    rows = ["Priya", "Anita", "Jordan", "Noah", "Sara"]
    cols = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    z = [[1, 1, 1, 1, 1], [1, 0, 1, 1, 0], [1, 1, 1, 1, 1], [0, 1, 0, 1, 0], [1, 1, 1, 1, 1]]
    fig = go.Figure(data=go.Heatmap(z=z, x=cols, y=rows, colorscale=[[0, "#fee2e2"], [1, "#dcfce7"]], showscale=False))
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8))
    st.plotly_chart(fig, use_container_width=True)
 
 
def radar_chart() -> None:
    categories = ["Confidence", "Momentum", "Blocker Load", "Feedback", "Update Consistency"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[3.6, 4.1, 2.5, 4.0, 4.8], theta=categories, fill="toself", name="Team"))
    fig.update_layout(height=340, margin=dict(l=8, r=8, t=10, b=8), polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
    st.plotly_chart(fig, use_container_width=True)
 
 
def alerts_page() -> None:
    top_bar("Alerts", "Prioritized notifications and risk events.")
    alerts = [
        ("Critical", "Noah's warehouse migration blocker is escalated and aging.", "risk-high"),
        ("Warning", "Anita's confidence has declined for three consecutive updates.", "risk-medium"),
        ("Info", "Weekly summary is ready for review.", "type-info"),
        ("Success", "Jordan resolved all assigned blockers.", "risk-low"),
    ]
    for level, message, kind in alerts:
        card(level, message, badge_html=badge(level, kind))
 
 
def mentor_dashboard() -> None:
    top_bar("Mentor Dashboard", "Review assigned mentees, trends, blockers, and feedback.")
    rows = fetch_team_dashboard()
    if not rows:
        st.info("No employee data available yet.")
        return
    names = [r["name"] for r in rows]
    mentee_name = st.selectbox("Mentee selector", names)
    selected = next((r for r in rows if r["name"] == mentee_name), rows[0])
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Updates", selected.get("total_updates", 0))
    k2.metric("Avg Confidence", selected.get("avg_confidence") or "N/A")
    k3.metric("Open blockers", selected.get("open_blockers", 0))
    k4.metric("Last update", _format_last_update(selected.get("last_update")))
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Weekly progress timeline")
        timeline()
    with right:
        feedback_composer(selected["name"])
        st.subheader("Feedback history")
        feedback_history()
 
def feedback_composer(employee: str | None = None, employee_id: int | None = None) -> None:
    st.subheader("Feedback composer")

    if employee_id is None:
        # Standalone page — build the dropdown from real employees, not a hardcoded list
        employees = [r for r in fetch_team_dashboard() if r.get("role") == "Employee"]
        if not employees:
            st.info("No employees found yet.")
            return
        name_to_id = {r["name"]: r["id"] for r in employees}
        target = employee or st.selectbox("Mentee", list(name_to_id.keys()))
        employee_id = name_to_id.get(target)
    else:
        target = employee

    with st.form(f"feedback_form_{employee or 'generic'}"):
        kind = st.segmented_control("Type", ["Praise", "Guidance", "Concern"], default="Guidance")
        visibility = st.radio("Visibility", ["Employee only", "Employee and manager"], horizontal=True)
        message = st.text_area("Message", max_chars=1000, placeholder="Write specific, actionable feedback...")
        st.caption(f"{len(message)} / 1000 characters")
        sent = st.form_submit_button(f"Send feedback to {target}", type="primary", use_container_width=True)

    if sent:
        if len(message.strip()) < 10:
            st.error("Feedback must be at least 10 characters.")
        elif not employee_id:
            st.error("Could not resolve the recipient's user id.")
        else:
            try:
                _post_json(
                    f"{API_BASE_URL}/api/v1/auth/feedback",
                    {
                        "from_user_id": st.session_state.user["id"],
                        "to_user_id": employee_id,
                        "type": kind.lower(),
                        "content": message,
                        "visibility": "employee_only" if visibility == "Employee only" else "employee_manager",
                    },
                    timeout=10,
                )
                st.success(f"{kind} feedback sent to {target}. Visibility: {visibility}.")
            except Exception as exc:
                st.error(f"Could not send feedback: {exc}")
def feedback_history() -> None:
    history = FEEDBACK[["Date", "From", "Type", "Message"]].rename(columns={"From": "Sender"})
    st.dataframe(history, hide_index=True, use_container_width=True)
 
 
def mentees_page() -> None:
    top_bar("Mentees", "Assigned mentees with current risk and update status.")
    display = team_dashboard_as_dataframe()
    if display.empty:
        st.info("No employee data available yet.")
    else:
        st.dataframe(display, hide_index=True, use_container_width=True)
 
 
def feedback_composer_page() -> None:
    top_bar("Feedback Composer", "Send praise, guidance, or concern feedback.")
    feedback_composer()
 
 
def feedback_history_page() -> None:
    top_bar("Feedback History", "Last 30 days of feedback.")
    feedback_history()
 
 
def route() -> None:
    user = st.session_state.user
    page = st.session_state.page
    if user["role"] == "Employee":
        {
            "Dashboard": employee_dashboard,
            "Daily Update": daily_update,
            "My Tasks": my_tasks,
            "Progress Timeline": progress_timeline_page,
            "Feedback Inbox": feedback_inbox_page,
            "My Risk": personal_risk_page,
        }[page]()
    elif user["role"] == "Mentor":
        {
            "Dashboard": mentor_dashboard,
            "Mentees": mentees_page,
            "Feedback Composer": feedback_composer_page,
            "Feedback History": feedback_history_page,
        }[page]()
    else:
        {
            "Dashboard": manager_dashboard,
            "Team Risk": team_risk_page,
            "Blockers": blockers_page,
            "AI Assistant": ai_assistant_page,
            "Weekly Summary": weekly_summary_page,
            "Analytics": analytics_page,
            "Alerts": alerts_page,
        }[page]()
 
 
def main() -> None:
    initialize_state()
    if not st.session_state.authenticated:
        login_screen()
        return
    inject_css()
    sidebar()
    route()
 
def fetch_blockers(status_filter: str | None = None, user_id: int | None = None) -> list[dict]:
    try:
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        if user_id is not None:
            params["user_id"] = user_id
        return _request_json(f"{API_BASE_URL}/api/v1/auth/blockers", params=params, timeout=10)
    except Exception:
        return []


def update_blocker_status(blocker_id: int, new_status: str) -> tuple[bool, str]:
    try:
        requests.put(
            f"{API_BASE_URL}/api/v1/auth/blockers/{blocker_id}/status",
            json={"status": new_status},
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        return False, str(exc)
    return True, f"Blocker_blockers #{blocker_id} marked {new_status}."


def blockers_page() -> None:
    top_bar("Active Blockers", "Track severity, age, status, ownership, and escalation.")
    rows = fetch_blockers()
    if not rows:
        st.info("No blockers found in the database yet.")
        return

    blockers_table()

    options = {f"#{r['id']} — {r.get('employee_name','?')}: {r['description'][:60]}": r["id"] for r in rows}
    selected_label = st.selectbox("Select a blocker to act on", list(options.keys()))
    selected_id = options[selected_label]

    c1, c2, c3 = st.columns(3)
    if c1.button("Escalate selected", use_container_width=True):
        ok, msg = update_blocker_status(selected_id, "escalated")
        (st.success if ok else st.error)(msg)
        st.cache_data.clear()
        st.rerun()
    if c2.button("Mark resolved", use_container_width=True):
        ok, msg = update_blocker_status(selected_id, "resolved")
        (st.success if ok else st.error)(msg)
        st.cache_data.clear()
        st.rerun()
    if c3.button("Reopen", use_container_width=True):
        ok, msg = update_blocker_status(selected_id, "open")
        (st.success if ok else st.error)(msg)
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()
