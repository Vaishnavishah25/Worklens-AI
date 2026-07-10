from __future__ import annotations
 
from datetime import date, datetime, timedelta
 
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
 
 
st.set_page_config(
    page_title="WorkLens AI",
    page_icon="WL",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
 
DEMO_USERS = {
    "manager@worklens.ai": {
        "password": "manager123",
        "name": "Maya Chen",
        "role": "Manager",
        "title": "Engineering Manager",
    },
    "mentor@worklens.ai": {
        "password": "mentor123",
        "name": "Ravi Mehta",
        "role": "Mentor",
        "title": "Staff Engineer",
    },
    "employee@worklens.ai": {
        "password": "employee123",
        "name": "Priya Shah",
        "role": "Employee",
        "title": "Backend Engineer",
    },
}
 
 
EMPLOYEES = pd.DataFrame(
    [
        {
            "Employee": "Priya Shah",
            "Role": "Backend Engineer",
            "Mentor": "Ravi Mehta",
            "Last Update": "Today, 9:14 AM",
            "Risk Score": 42,
            "Risk": "Medium",
            "Risk Trend": "Rising",
            "Open Blockers": 1,
            "Overdue Tasks": 1,
            "Confidence": 3.6,
        },
        {
            "Employee": "Anita Rao",
            "Role": "Frontend Engineer",
            "Mentor": "Ravi Mehta",
            "Last Update": "Yesterday, 5:40 PM",
            "Risk Score": 76,
            "Risk": "High",
            "Risk Trend": "Rising",
            "Open Blockers": 2,
            "Overdue Tasks": 3,
            "Confidence": 2.1,
        },
        {
            "Employee": "Jordan Lee",
            "Role": "Platform Engineer",
            "Mentor": "Elena Torres",
            "Last Update": "Today, 10:02 AM",
            "Risk Score": 24,
            "Risk": "Low",
            "Risk Trend": "Stable",
            "Open Blockers": 0,
            "Overdue Tasks": 0,
            "Confidence": 4.4,
        },
        {
            "Employee": "Noah Williams",
            "Role": "Data Engineer",
            "Mentor": "Elena Torres",
            "Last Update": "2 days ago",
            "Risk Score": 63,
            "Risk": "High",
            "Risk Trend": "Rising",
            "Open Blockers": 2,
            "Overdue Tasks": 2,
            "Confidence": 2.7,
        },
        {
            "Employee": "Sara Ahmed",
            "Role": "QA Engineer",
            "Mentor": "Ravi Mehta",
            "Last Update": "Today, 8:52 AM",
            "Risk Score": 31,
            "Risk": "Low",
            "Risk Trend": "Improving",
            "Open Blockers": 0,
            "Overdue Tasks": 1,
            "Confidence": 4.1,
        },
    ]
)
 
 
BLOCKERS = pd.DataFrame(
    [
        {
            "Employee": "Anita Rao",
            "Blocker": "Waiting on design tokens for onboarding flow",
            "Severity": "High",
            "Age": "4d",
            "Status": "Open",
        },
        {
            "Employee": "Noah Williams",
            "Blocker": "Warehouse schema migration blocked by permissions",
            "Severity": "Critical",
            "Age": "2d",
            "Status": "Escalated",
        },
        {
            "Employee": "Priya Shah",
            "Blocker": "API contract still changing for billing service",
            "Severity": "Medium",
            "Age": "1d",
            "Status": "Open",
        },
        {
            "Employee": "Anita Rao",
            "Blocker": "E2E test data missing for SSO edge cases",
            "Severity": "Medium",
            "Age": "3d",
            "Status": "Open",
        },
    ]
)
 
 
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
            submitted = st.form_submit_button("Log in", width="stretch", type="primary")
        with st.expander("Demo credentials", expanded=True):
            st.code(
                "Manager  manager@worklens.ai / manager123\n"
                "Mentor   mentor@worklens.ai / mentor123\n"
                "Employee employee@worklens.ai / employee123",
                language="text",
            )
        if submitted:
            user = DEMO_USERS.get(email.strip().lower())
            if user and user["password"] == password:
                st.session_state.authenticated = True
                st.session_state.user = {**user, "email": email.strip().lower(), "remember": remember}
                st.session_state.page = "Dashboard"
                st.rerun()
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
        if st.sidebar.button(item, key=f"nav_{item}", width="stretch"):
            st.session_state.page = item
    st.sidebar.divider()
    st.sidebar.caption(f"{user['name']} · {user['title']}")
    if st.sidebar.button("Logout", width="stretch"):
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
        if st.button("Submit daily update", type="primary", width="stretch"):
            st.session_state.page = "Daily Update"
            st.rerun()
        st.button("View last update", width="stretch")
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
 
 
def daily_update() -> None:
    top_bar("Daily Update", "Capture work done, blockers, next steps, and confidence.")
    with st.form("daily_update_form"):
        work_done = st.text_area("Work Done", placeholder="What did you complete or make progress on today?", height=130)
        no_blockers = st.checkbox("No blockers today")
        blocker = st.text_area("Blockers", placeholder="What is blocking or slowing you down?", height=100, disabled=no_blockers)
        severity = st.segmented_control("Severity", ["None", "Low", "Medium", "High", "Critical"], default="None")
        next_steps = st.text_area("Next Steps", placeholder="What are you planning to do next?", height=100)
        confidence = st.slider("Confidence", min_value=1, max_value=5, value=4)
        submitted = st.form_submit_button("Submit update", type="primary", width="stretch")
    if submitted:
        if not work_done or not next_steps:
            st.error("Please complete Work Done and Next Steps before submitting.")
        elif severity != "None" and not no_blockers and not blocker:
            st.error("Please describe the blocker or select 'No blockers today'.")
        else:
            st.session_state.submitted_update = {
                "work_done": work_done,
                "blocker": "No blockers today" if no_blockers else blocker,
                "severity": severity,
                "next_steps": next_steps,
                "confidence": confidence,
                "submitted_at": datetime.now().strftime("%I:%M %p"),
            }
            st.success("Update submitted. Your manager and mentor can now see today's progress.")
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
                    c3.button("Mark done", key=f"done_{row['Task']}")
                    c3.button("Report blocker", key=f"blocker_{row['Task']}")
 
 
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
 
 
def feedback_list() -> None:
    for _, row in FEEDBACK.iterrows():
        kind = {"Praise": "risk-low", "Guidance": "type-info", "Concern": "risk-medium"}[row["Type"]]
        unread = " · unread" if row["Unread"] else ""
        st.markdown(
            f"""
            <div class="wl-card wl-tight" style="margin-bottom:10px;">
                <div class="wl-row">
                    <b>{row['From']}</b>{badge(row['Type'], kind)}
                </div>
                <div class="wl-muted">{row['Date']}{unread}</div>
                <div style="margin-top:8px;">{row['Message']}</div>
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
    left, right = st.columns([.95, 1.15], gap="large")
    with left:
        feedback_list()
    with right:
        card(
            "Selected feedback",
            "Good progress on the adapter. Please call out billing API churn early in tomorrow's update.",
            "Guidance from Ravi Mehta",
            badge("Unread", "type-info"),
        )
 
 
def personal_risk_page() -> None:
    top_bar("My Risk", "Transparent, explainable risk scoring focused on support.")
    left, right = st.columns([.9, 1.1], gap="large")
    with left:
        personal_risk_widget()
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
    display = EMPLOYEES.copy()
    display["Risk Label"] = display["Risk"]
    st.dataframe(
        display[["Employee", "Last Update", "Risk Score", "Risk Label", "Risk Trend", "Open Blockers", "Overdue Tasks"]],
        hide_index=True,
        width="stretch",
    )
    st.caption("Actions: view profile, prepare 1:1, message mentor, ask AI, create action item.")
 
 
def blockers_table() -> None:
    st.dataframe(BLOCKERS, hide_index=True, width="stretch")
    st.caption("Critical and aging blockers should be triaged first.")
 
 
def weekly_summary_card() -> None:
    st.markdown(
        """
        <div class="wl-card">
            <div class="wl-row">
                <h3 style="margin:0;">Weekly Summary</h3>
                <span class="wl-badge type-ai">AI generated</span>
            </div>
            <div class="wl-divider"></div>
            <b>Highlights</b>
            <ul><li>Update completion improved to 91%.</li><li>Two blockers were resolved within 24 hours.</li></ul>
            <b>Concerns</b>
            <ul><li>Frontend and data workstreams show rising risk.</li><li>Critical warehouse permission blocker is aging.</li></ul>
            <b>Recommendations</b>
            <ul><li>Schedule 1:1s with Anita and Noah.</li><li>Assign an owner to unblock warehouse permissions today.</li></ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def ai_recommendations() -> None:
    st.markdown(
        """
        <div class="wl-card wl-ai-response">
            <div class="wl-eyebrow">AI WorkLens Assistant</div>
            <h3 style="margin:.1rem 0;">Who needs immediate help?</h3>
            <p>Anita Rao and Noah Williams show the strongest intervention signals based on blocker age, confidence decline, and overdue tasks.</p>
            <div class="wl-muted">Sources: daily updates, active blockers, risk scores</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
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
    c1.button("Assign owner", width="stretch")
    c2.button("Escalate selected", width="stretch")
    c3.button("Mark resolved", width="stretch")
 
 
def ai_assistant_page() -> None:
    top_bar("AI WorkLens Assistant", "Ask cited questions about delivery risk, blockers, and team health.")
    history, chat, sources = st.columns([.75, 1.6, .9], gap="large")
    with history:
        st.subheader("History")
        for item in ["Sprint risk review", "1:1 prep for Anita", "Weekly blocker summary"]:
            st.button(item, width="stretch")
        st.subheader("Suggested prompts")
        for prompt in ["Who needs immediate help?", "What is blocking the sprint?", "Prepare my 1:1s.", "Why is team health declining?"]:
            st.caption(prompt)
    with chat:
        st.markdown('<div class="wl-chat"><b>You</b><br>Who needs immediate help?</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="wl-chat wl-ai-response">
                <b>WorkLens AI</b>
                <p>Two team members need immediate support: Anita Rao and Noah Williams.</p>
                <ol>
                    <li><b>Anita Rao</b>: risk increased to 76 with two blockers and declining confidence.</li>
                    <li><b>Noah Williams</b>: critical warehouse permission blocker is escalated and two days old.</li>
                </ol>
                <p><b>Recommended actions:</b> schedule focused 1:1s, assign unblock owners, and review overdue work scope.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.chat_input("Ask about risks, blockers, updates, or 1:1 prep...")
    with sources:
        st.subheader("Sources")
        card("Daily updates", "5 updates reviewed from the current sprint.", badge_html=badge("Cited", "type-ai"))
        card("Blockers", "4 open blockers, including 1 critical escalation.", badge_html=badge("Live", "risk-medium"))
        card("Risk scores", "Latest generated scores for all team members.", badge_html=badge("Fresh", "type-teal"))
 
 
def weekly_summary_page() -> None:
    top_bar("Weekly Summary", "AI-generated highlights, concerns, and recommendations.")
    weekly_summary_card()
    c1, c2, c3, c4 = st.columns(4)
    c1.button("Regenerate", width="stretch")
    c2.button("Copy", width="stretch")
    c3.button("Export", width="stretch")
    c4.button("Send to Slack", width="stretch")
 
 
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
 
 
def trend_chart() -> None:
    days = [date.today() - timedelta(days=i) for i in range(13, -1, -1)]
    values = [72, 73, 71, 69, 70, 74, 76, 78, 77, 75, 76, 78, 79, 78]
    fig = px.line(x=days, y=values, markers=True, labels={"x": "Date", "y": "Score"})
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8), showlegend=False)
    st.plotly_chart(fig, width="stretch")
 
 
def risk_distribution_chart() -> None:
    fig = px.pie(names=["Low", "Medium", "High"], values=[2, 1, 2], hole=.58, color=["Low", "Medium", "High"], color_discrete_map={"Low": "#16a34a", "Medium": "#f59e0b", "High": "#dc2626"})
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8))
    st.plotly_chart(fig, width="stretch")
 
 
def blocker_chart() -> None:
    data = pd.DataFrame({"Week": ["W1", "W2", "W3", "W4"], "Low": [2, 1, 3, 1], "Medium": [3, 4, 2, 3], "High": [1, 2, 2, 3], "Critical": [0, 1, 0, 1]})
    fig = px.bar(data, x="Week", y=["Low", "Medium", "High", "Critical"], barmode="stack")
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8), legend_title_text="")
    st.plotly_chart(fig, width="stretch")
 
 
def heatmap_chart() -> None:
    rows = ["Priya", "Anita", "Jordan", "Noah", "Sara"]
    cols = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    z = [[1, 1, 1, 1, 1], [1, 0, 1, 1, 0], [1, 1, 1, 1, 1], [0, 1, 0, 1, 0], [1, 1, 1, 1, 1]]
    fig = go.Figure(data=go.Heatmap(z=z, x=cols, y=rows, colorscale=[[0, "#fee2e2"], [1, "#dcfce7"]], showscale=False))
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=10, b=8))
    st.plotly_chart(fig, width="stretch")
 
 
def radar_chart() -> None:
    categories = ["Confidence", "Momentum", "Blocker Load", "Feedback", "Update Consistency"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[3.6, 4.1, 2.5, 4.0, 4.8], theta=categories, fill="toself", name="Team"))
    fig.update_layout(height=340, margin=dict(l=8, r=8, t=10, b=8), polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
    st.plotly_chart(fig, width="stretch")
 
 
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
    mentee = st.selectbox("Mentee selector", ["Priya Shah", "Anita Rao", "Sara Ahmed"])
    selected = EMPLOYEES[EMPLOYEES["Employee"] == mentee].iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Risk score", selected["Risk Score"], selected["Risk"])
    k2.metric("Confidence", selected["Confidence"], selected["Risk Trend"])
    k3.metric("Open blockers", selected["Open Blockers"])
    k4.metric("Last update", selected["Last Update"])
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Weekly progress timeline")
        timeline()
    with right:
        feedback_composer(selected["Employee"])
        st.subheader("Feedback history")
        feedback_history()
 
 
def feedback_composer(employee: str | None = None) -> None:
    st.subheader("Feedback composer")
    with st.form(f"feedback_form_{employee or 'generic'}"):
        target = employee or st.selectbox("Mentee", ["Priya Shah", "Anita Rao", "Sara Ahmed"])
        kind = st.segmented_control("Type", ["Praise", "Guidance", "Concern"], default="Guidance")
        visibility = st.radio("Visibility", ["Employee only", "Employee and manager"], horizontal=True)
        message = st.text_area("Message", max_chars=1000, placeholder="Write specific, actionable feedback...")
        st.caption(f"{len(message)} / 1000 characters")
        sent = st.form_submit_button(f"Send feedback to {target}", type="primary", width="stretch")
    if sent:
        if len(message.strip()) < 10:
            st.error("Feedback must be at least 10 characters.")
        else:
            st.success(f"{kind} feedback sent to {target}. Visibility: {visibility}.")
 
 
def feedback_history() -> None:
    history = FEEDBACK[["Date", "From", "Type", "Message"]].rename(columns={"From": "Sender"})
    st.dataframe(history, hide_index=True, width="stretch")
 
 
def mentees_page() -> None:
    top_bar("Mentees", "Assigned mentees with current risk and update status.")
    st.dataframe(EMPLOYEES[EMPLOYEES["Mentor"] == "Ravi Mehta"], hide_index=True, width="stretch")
 
 
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
 
 
if __name__ == "__main__":
    main()
 
 