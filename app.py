"""
app.py
------
Streamlit frontend for the Agentic Concierge insurance chatbot.
Run with: streamlit run app.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

import streamlit as st

# ── Make the src package importable regardless of working directory ──
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from agentic_concierge.concierge_agent import ConciergeAgent

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Concierge | Insurance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* App background */
    .stApp { background-color: #f0f4f8; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a2744;
        color: white;
    }
    /* Only color labels, headers, and markdown text white — NOT input field text */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span:not(input ~ span),
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }

    /* Text typed into input boxes and text areas must stay dark and visible */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        color: #1a2744 !important;
        background-color: white !important;
        -webkit-text-fill-color: #1a2744 !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: #2e4080;
        color: white !important;
        border: 1px solid #4a5fa0;
        border-radius: 8px;
        width: 100%;
        margin-bottom: 4px;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #3d55a8;
    }

    /* Customer info card in sidebar */
    .customer-card {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .customer-card h3 { font-size: 1rem; margin: 0 0 8px 0; }
    .customer-card p  { font-size: 0.82rem; margin: 2px 0; }

    /* Chat bubbles */
    .user-bubble {
        background: #2e4080;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 10px 16px;
        margin: 6px 0 6px 20%;
        text-align: right;
    }
    .bot-bubble {
        background: white;
        color: #1a2744;
        border-radius: 18px 18px 18px 4px;
        padding: 10px 16px;
        margin: 6px 20% 6px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }

    /* Intent badge */
    .intent-badge {
        display: inline-block;
        background: #e8edf7;
        color: #2e4080;
        border-radius: 20px;
        font-size: 0.72rem;
        padding: 2px 10px;
        margin-top: 4px;
    }

    /* Escalation warning */
    .escalation-banner {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        color: #856404;
    }

    /* App title */
    .app-title { color: #1a2744; font-size: 1.8rem; font-weight: 700; }

    /* Auth box */
    .auth-box {
        background: white;
        border-radius: 12px;
        padding: 30px;
        max-width: 480px;
        margin: 40px auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state initialisation ─────────────────────────────────────
if "agent" not in st.session_state:
    data_dir = str(ROOT / "data")
    st.session_state.agent = ConciergeAgent(data_dir=data_dir)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "customer_data" not in st.session_state:
    st.session_state.customer_data = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_escalation" not in st.session_state:
    st.session_state.show_escalation = False


# ── Helper functions ──────────────────────────────────────────────────

def process_user_message(text: str) -> None:
    """Run a message through the agent and append results to session messages."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": text, "intent": None})

    # Get agent response
    result = st.session_state.agent.process_message(text)

    # Add bot response
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["response"],
        "intent":  result.get("intent", ""),
    })

    # Check escalation flag
    if result.get("escalation_needed"):
        st.session_state.show_escalation = True


def handle_escalation() -> None:
    """Trigger a manual escalation via the button."""
    result = st.session_state.agent.process_message("I want to speak to a human agent")
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["response"],
        "intent":  "ESCALATION",
    })
    st.session_state.show_escalation = False


def display_message(role: str, content: str, intent: str = None) -> None:
    """Render a single chat message as a styled bubble."""
    if role == "user":
        st.markdown(
            f'<div class="user-bubble">{content}</div>',
            unsafe_allow_html=True,
        )
    else:
        badge = ""
        if intent and intent not in ("", "UNKNOWN", "GREETING"):
            label = intent.replace("_", " ").title()
            badge = f'<br><span class="intent-badge">🤖 {label}</span>'
        st.markdown(
            f'<div class="bot-bubble">{content}{badge}</div>',
            unsafe_allow_html=True,
        )


# ── SIDEBAR ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Agentic Concierge")
    st.markdown("*Insurance Service Center*")
    st.markdown("---")

    if not st.session_state.authenticated:
        # Authentication panel
        st.markdown("### 🔐 Login")
        policy_input = st.text_input(
            "Policy Number",
            placeholder="e.g. AZ-2026-1001",
            key="policy_input",
        )
        if st.button("Login", key="login_btn"):
            if policy_input.strip():
                auth_result = st.session_state.agent.authenticate(policy_input.strip())
                if auth_result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.customer_data = auth_result["customer"]
                    st.session_state.messages = [{
                        "role":    "assistant",
                        "content": auth_result["welcome_message"],
                        "intent":  "GREETING",
                    }]
                    st.rerun()
                else:
                    st.error("Policy not found. Try AZ-2026-1001 or AZ-2026-1002")
                    st.info(auth_result["welcome_message"])
            else:
                st.warning("Please enter a policy number.")

        st.markdown("---")
        st.markdown("**Demo accounts:**")
        st.markdown("• `AZ-2026-1001` — Aisha Patel (Auto)")
        st.markdown("• `AZ-2026-1002` — Luis Garcia (Home)")

    else:
        # Customer info card
        c = st.session_state.customer_data
        st.markdown(
            f"""
            <div class="customer-card">
                <h3>👤 {c.get('first_name')} {c.get('last_name')}</h3>
                <p>📋 {c.get('policy_number')}</p>
                <p>📧 {c.get('email')}</p>
                <p>📞 {c.get('phone')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚡ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Policy", key="q_policy"):
                process_user_message("What is my policy coverage?")
                st.rerun()
        with col2:
            if st.button("📊 Claims", key="q_claims"):
                process_user_message("What is the status of my claim?")
                st.rerun()
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💰 Payment", key="q_payment"):
                process_user_message("When is my next payment due?")
                st.rerun()
        with col4:
            if st.button("🔄 Renewal", key="q_renewal"):
                process_user_message("When does my policy renew?")
                st.rerun()

        st.markdown("---")
        st.markdown("### 🔧 Session")
        if st.button("🆕 New Session", key="reset_btn"):
            st.session_state.agent.reset_session()
            st.session_state.authenticated  = False
            st.session_state.customer_data  = {}
            st.session_state.messages       = []
            st.session_state.show_escalation = False
            st.rerun()

        if st.checkbox("📈 Session Summary"):
            summary = st.session_state.agent.get_conversation_summary()
            st.text_area("Summary", summary, height=200, key="summary_box")


# ── MAIN AREA ─────────────────────────────────────────────────────────
st.markdown('<h1 class="app-title">🛡️ Agentic Concierge</h1>', unsafe_allow_html=True)
st.markdown("**Insurance Service Center** — Your 24/7 AI-Powered Assistant")
st.markdown("---")

if not st.session_state.authenticated:
    # Pre-login landing
    st.markdown(
        """
        <div class="auth-box">
            <h2>Welcome!</h2>
            <p>Please enter your <strong>Policy Number</strong> in the sidebar to get started.</p>
            <p style="color:#666; font-size:0.9rem;">
            Demo: use <code>AZ-2026-1001</code> or <code>AZ-2026-1002</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    # Chat interface
    # Display conversation history
    if st.session_state.messages:
        for msg in st.session_state.messages:
            display_message(msg["role"], msg["content"], msg.get("intent"))
    else:
        st.info("👋 Chat started. How can I help you today?")

    st.markdown("---")

    # Escalation banner
    if st.session_state.show_escalation:
        st.markdown(
            """
            <div class="escalation-banner">
                ⚠️ <strong>It looks like you need additional help.</strong>
                Click below to connect with a human agent.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Connect with Human Agent", key="escalate_btn"):
            handle_escalation()
            st.rerun()

    # Chat input — wrapped in a form so it clears on submit and only
    # fires once per click/Enter, instead of resubmitting on every rerun
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Your message",
            placeholder="Type your question here… (e.g. 'What is my coverage?' or 'I had an accident')",
            key="chat_input",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send")

    if submitted and user_input and user_input.strip():
        process_user_message(user_input.strip())
        st.rerun()

    # Footer
    st.markdown(
        f"""
        <div style="text-align:center; color:#aaa; font-size:0.78rem; margin-top:20px;">
        🛡️ Agentic Concierge | Powered by GitHub Copilot |
        Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True,
    )
