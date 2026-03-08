"""
Streamlit Frontend for Resume Tailor Agent.

Run with: streamlit run frontend.py
Make sure the backend is running: uvicorn app.main:app --reload

STREAMING VERSION:
Uses the /agent/stream endpoint to show each reasoning step
in real-time as the agent works, instead of waiting for everything.
"""

import streamlit as st
import requests
import json
import time
import html

# ─── Config ───────────────────────────────────────────────
API_BASE = "http://localhost:8000"

# ─── Page Setup ───────────────────────────────────────────
st.set_page_config(
    page_title="Resume Tailor Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;400;500;600;700&display=swap');

    * { font-family: 'DM Sans', sans-serif; }

    .main .block-container {
        max-width: 880px;
        padding-top: 1.5rem;
    }

    /* Header */
    .agent-header {
        background: #ffffff;
        border: 1px solid #e8e8ec;
        padding: 1.8rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.2rem;
        color: #1a1a2e;
    }
    .agent-header h1 {
        margin: 0;
        font-size: 1.55rem;
        font-weight: 700;
        letter-spacing: -0.4px;
        color: #1a1a2e;
    }
    .agent-header p {
        margin: 0.25rem 0 0 0;
        color: #6b7280;
        font-size: 0.88rem;
        font-weight: 400;
    }
    .agent-header .badge {
        display: inline-block;
        background: #f0f0f5;
        border: 1px solid #e0e0e8;
        padding: 0.2rem 0.65rem;
        border-radius: 6px;
        font-size: 0.68rem;
        font-weight: 600;
        margin-top: 0.6rem;
        letter-spacing: 0.4px;
        color: #6b7280;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        margin-right: 6px;
        position: relative;
        top: -1px;
    }
    .status-online { background: #22c55e; }
    .status-offline { background: #ef4444; }

    /* Sidebar refinement */
    section[data-testid="stSidebar"] {
        background: #fafafa;
        border-right: 1px solid #ebebef;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #9ca3af;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    /* Chat input styling */
    .stChatInput > div {
        border-radius: 12px !important;
        border: 1px solid #e0e0e8 !important;
    }
    .stChatInput textarea {
        font-size: 0.92rem !important;
    }

    /* Step cards */
    .step-card {
        background: #f8f9fb;
        border: 1px solid #e8e8ec;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        font-size: 0.88rem;
        line-height: 1.5;
        color: #374151;
    }
    .step-card .step-label {
        font-weight: 600;
        color: #1a1a2e;
        font-size: 0.82rem;
    }
    .step-card .step-thought {
        color: #6b7280;
        font-style: italic;
        margin-top: 0.25rem;
        font-size: 0.84rem;
    }

    /* Completion card */
    .done-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
        color: #166534;
        font-size: 0.9rem;
        line-height: 1.55;
    }
    .done-card strong { color: #15803d; }

    /* Thinking pulse */
    .thinking-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 10px;
        padding: 0.75rem 1.1rem;
        font-size: 0.86rem;
        color: #92400e;
        animation: pulse-border 1.8s ease-in-out infinite;
    }
    @keyframes pulse-border {
        0%, 100% { border-color: #fde68a; }
        50% { border-color: #fbbf24; }
    }

    /* Info tips */
    .tip-card {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 0.75rem 1.1rem;
        font-size: 0.86rem;
        color: #1e40af;
        margin-bottom: 0.8rem;
    }

    /* Error card */
    .error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 10px;
        padding: 0.75rem 1.1rem;
        font-size: 0.86rem;
        color: #991b1b;
    }

    /* Override Streamlit expander */
    .streamlit-expanderHeader {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
    }

    /* Hide default Streamlit decoration */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────

def check_backend():
    """Check if the FastAPI backend is running."""
    try:
        r = requests.get(f"{API_BASE}/", timeout=3)
        return r.status_code == 200
    except:
        return False


# Tool icon mapping
TOOL_ICONS = {
    "analyze_job": "🔍",
    "load_identity": "👤",
    "research_company": "🏢",
    "build_resume": "📝",
    "generate_pdf": "📄",
    "review_resume": "📋",
    "search_ddg": "🦆",
    "search_brave": "🦁",
}


# ─── Sidebar ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Settings")

    # Backend status
    backend_online = check_backend()
    if backend_online:
        st.markdown('<span class="status-dot status-online"></span> Backend **Online**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot status-offline"></span> Backend **Offline**', unsafe_allow_html=True)
        st.error("Start the backend:\n`uvicorn app.main:app --reload`")

    st.divider()

    # Tool toggles
    st.markdown("### Search")
    web_search_enabled = st.toggle("Web Search", value=True, help="Enable or disable web search (Brave + DuckDuckGo)")
    st.caption("Let the agent search the web for company info, salary data, etc.")

    st.divider()

    # Quick actions
    st.markdown("### Quick Actions")
    quick_action = st.selectbox(
        "Pick a preset goal:",
        [
            "Custom (type your own)",
            "Tailor my resume for a job",
            "Review my current CV",
            "Research a company",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Resume Tailor v2.0 · Qwen3-4B via Ollama")


# ─── Main Content ─────────────────────────────────────────

# Header
st.markdown("""
<div class="agent-header">
    <h1>Resume Tailor</h1>
    <p>Tell me what you need — I'll figure out the rest.</p>
    <span class="badge">QWEN3-4B · LOCAL · GPU ACCELERATED</span>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "agent":
        with st.chat_message("assistant", avatar="🤖"):
            # Show steps from history
            for step in msg.get("steps", []):
                if step["type"] == "step":
                    icon = TOOL_ICONS.get(step.get("action", ""), "·")
                    action_safe = html.escape(step.get("action", ""))
                    thought_safe = html.escape(step.get("thought", ""))
                    st.markdown(
                        f'<div class="step-card">'
                        f'<div class="step-label">Step {step["iteration"]} — {icon} {action_safe}</div>'
                        f'<div class="step-thought">{thought_safe}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"View {step['action']} result"):
                        st.json(step.get("result", {}))
            # Show final answer
            if msg.get("summary"):
                st.markdown(f'<div class="done-card"><strong>Done</strong> — {html.escape(msg["summary"])}</div>', unsafe_allow_html=True)
            if msg.get("pdf_path"):
                st.markdown(f'<div class="done-card">PDF saved → <code>{html.escape(msg["pdf_path"])}</code></div>', unsafe_allow_html=True)

# Handle quick action presets
if quick_action == "Tailor my resume for a job":
    st.markdown('<div class="tip-card">Paste a job description or URL below, starting with: <strong>Tailor my resume for this job:</strong></div>', unsafe_allow_html=True)
elif quick_action == "Review my current CV":
    st.markdown('<div class="tip-card">Paste a job description below, starting with: <strong>Review my CV against this job:</strong></div>', unsafe_allow_html=True)
elif quick_action == "Research a company":
    st.markdown('<div class="tip-card">Type below: <strong>Research [company name] and tell me about them</strong></div>', unsafe_allow_html=True)

# Chat input
goal = st.chat_input("What would you like me to do? (e.g., 'Tailor my resume for...')")

# Process new input
if goal:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": goal})

    with st.chat_message("user"):
        st.write(goal)

    # Run the agent with streaming
    with st.chat_message("assistant", avatar="🤖"):
        if not backend_online:
            st.error("Backend is offline. Start it first!")
        else:
            config = {"web_search": web_search_enabled}

            # Container for live steps
            status_container = st.empty()
            steps_container = st.container()
            final_container = st.empty()

            collected_steps = []
            final_summary = ""
            pdf_path = None

            try:
                # Stream from the backend
                response = requests.post(
                    f"{API_BASE}/resume/agent/stream",
                    json={"goal": goal, "config": config},
                    stream=True,
                    timeout=300,
                )

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")
                    iteration = event.get("iteration", "?")

                    if event_type == "thinking":
                        # Show pulsing "thinking" status
                        status_container.markdown(f'<div class="thinking-card"><strong>Step {html.escape(str(iteration))}</strong> — Agent is thinking\u2026</div>', unsafe_allow_html=True)

                    elif event_type == "step":
                        # Clear the "thinking" status
                        status_container.empty()

                        action = event.get("action", "unknown")
                        thought = event.get("thought", "")
                        result = event.get("result", {})
                        icon = TOOL_ICONS.get(action, "·")
                        action_safe = html.escape(action)
                        thought_safe = html.escape(thought)

                        # Display the step live
                        with steps_container:
                            st.markdown(
                                f'<div class="step-card">'
                                f'<div class="step-label">Step {iteration} — {icon} {action_safe}</div>'
                                f'<div class="step-thought">{thought_safe}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            with st.expander(f"View {action} result"):
                                st.json(result)

                        collected_steps.append(event)

                    elif event_type == "error":
                        status_container.empty()
                        with steps_container:
                            st.markdown(f'<div class="error-card"><strong>Step {html.escape(str(iteration))}</strong> — {html.escape(event.get("message", "Error"))}</div>', unsafe_allow_html=True)
                        collected_steps.append(event)

                    elif event_type == "done":
                        status_container.empty()
                        final_summary = event.get("summary", "Task completed.")
                        pdf_path = event.get("pdf_path")

                        final_container.markdown(f'<div class="done-card"><strong>Done</strong> — {html.escape(final_summary)}</div>', unsafe_allow_html=True)
                        if pdf_path:
                            st.markdown(f'<div class="done-card">PDF saved → <code>{html.escape(pdf_path)}</code></div>', unsafe_allow_html=True)

                        collected_steps.append(event)

                # Save to session state for history
                st.session_state.messages.append({
                    "role": "agent",
                    "content": final_summary,
                    "steps": collected_steps,
                    "summary": final_summary,
                    "pdf_path": pdf_path,
                })

            except requests.exceptions.Timeout:
                status_container.empty()
                st.error("⏱️ The agent took too long to respond. Try a simpler goal.")
            except requests.exceptions.ConnectionError:
                status_container.empty()
                st.error("❌ Can't connect to backend. Make sure it's running.")
            except Exception as e:
                status_container.empty()
                st.error(f"❌ Error: {str(e)}")
