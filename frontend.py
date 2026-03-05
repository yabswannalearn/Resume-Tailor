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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }

    /* Header */
    .agent-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .agent-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .agent-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.7;
        font-size: 0.9rem;
    }
    .agent-header .badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.2);
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        margin-top: 0.5rem;
        letter-spacing: 0.5px;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-online { background: #a6e3a1; }
    .status-offline { background: #f38ba8; }
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
    st.markdown("### ⚙️ Agent Settings")

    # Backend status
    backend_online = check_backend()
    if backend_online:
        st.markdown('<span class="status-dot status-online"></span> Backend **Online**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot status-offline"></span> Backend **Offline**', unsafe_allow_html=True)
        st.error("Start the backend:\n`uvicorn app.main:app --reload`")

    st.divider()

    # Tool toggles
    st.markdown("### 🔧 Search Tools")
    web_search_enabled = st.toggle("🔍 Web Search", value=True, help="Enable or disable web search (Brave + DuckDuckGo)")
    st.caption("When enabled, the agent can search the web for company info, salary data, etc.")

    st.divider()

    # Quick actions
    st.markdown("### 🚀 Quick Actions")
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
    st.caption("Resume Tailor Agent v2.0")
    st.caption("Powered by Qwen3-4B via Ollama")


# ─── Main Content ─────────────────────────────────────────

# Header
st.markdown("""
<div class="agent-header">
    <h1>🤖 Resume Tailor Agent</h1>
    <p>Tell me what you need — I'll figure out the rest.</p>
    <span class="badge">QWEN3-4B • LOCAL • GPU ACCELERATED</span>
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
                    icon = TOOL_ICONS.get(step.get("action", ""), "🔧")
                    st.info(f"**Step {step['iteration']}** — {icon} `{step['action']}`\n\n💭 _{step.get('thought', '')}_")
                    with st.expander(f"View {step['action']} result"):
                        st.json(step.get("result", {}))
            # Show final answer
            if msg.get("summary"):
                st.success(f"✅ **Agent Complete**\n\n{msg['summary']}")
            if msg.get("pdf_path"):
                st.success(f"📄 PDF generated: `{msg['pdf_path']}`")

# Handle quick action presets
if quick_action == "Tailor my resume for a job":
    st.info("💡 Paste a job description or URL in the chat box below, starting with: **Tailor my resume for this job:**")
elif quick_action == "Review my current CV":
    st.info("💡 Paste a job description in the chat box, starting with: **Review my CV against this job:**")
elif quick_action == "Research a company":
    st.info("💡 Type in the chat box: **Research [company name] and tell me about them**")

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
                        status_container.warning(f"🧠 **Step {iteration}** — Agent is thinking...")

                    elif event_type == "step":
                        # Clear the "thinking" status
                        status_container.empty()

                        action = event.get("action", "unknown")
                        thought = event.get("thought", "")
                        result = event.get("result", {})
                        icon = TOOL_ICONS.get(action, "🔧")

                        # Display the step live
                        with steps_container:
                            st.info(f"**Step {iteration}** — {icon} `{action}`\n\n💭 _{thought}_")
                            with st.expander(f"View {action} result"):
                                st.json(result)

                        collected_steps.append(event)

                    elif event_type == "error":
                        status_container.empty()
                        with steps_container:
                            st.warning(f"⚠️ **Step {iteration}** — {event.get('message', 'Error')}")
                        collected_steps.append(event)

                    elif event_type == "done":
                        status_container.empty()
                        final_summary = event.get("summary", "Task completed.")
                        pdf_path = event.get("pdf_path")

                        final_container.success(f"✅ **Agent Complete**\n\n{final_summary}")
                        if pdf_path:
                            st.success(f"📄 PDF generated: `{pdf_path}`")

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
