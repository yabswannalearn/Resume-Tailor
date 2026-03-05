"""
Streamlit Frontend for Resume Tailor Agent.

Run with: streamlit run frontend.py
Make sure the backend is running: uvicorn app.main:app --reload
"""

import streamlit as st
import requests
import json

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

    /* Step cards */
    .step-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .step-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .step-number {
        background: linear-gradient(135deg, #89b4fa, #74c7ec);
        color: #1e1e2e;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
    }
    .step-action {
        color: #cba6f7;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .step-thought {
        color: #a6adc8;
        font-size: 0.82rem;
        font-style: italic;
        margin-bottom: 0.3rem;
    }

    /* Final answer */
    .final-card {
        background: linear-gradient(135deg, #1e3a2f, #1e2e1e);
        border: 1px solid #a6e3a1;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 1rem;
    }
    .final-card h4 {
        color: #a6e3a1;
        margin: 0 0 0.5rem 0;
    }
    .final-card p {
        color: #cdd6f4;
        line-height: 1.6;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #181825;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #cdd6f4;
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


def run_agent(goal: str, config: dict) -> dict:
    """Send a goal to the agent endpoint."""
    response = requests.post(
        f"{API_BASE}/resume/agent",
        json={"goal": goal, "config": config},
        timeout=300,  # Agent can take a while with local models
    )
    return response.json()


def render_step(step: dict, index: int):
    """Render an agent reasoning step as a styled card."""
    action = step.get("action", "unknown")
    thought = step.get("thought", "")

    if action == "final_answer":
        summary = step.get("summary", "")
        st.markdown(f"""
        <div class="final-card">
            <h4>✅ Agent Complete</h4>
            <p>{summary}</p>
        </div>
        """, unsafe_allow_html=True)
    elif action == "parse_error":
        st.markdown(f"""
        <div class="step-card" style="border-color: #f38ba8;">
            <div class="step-header">
                <span class="step-number">Step {index}</span>
                <span class="step-action" style="color: #f38ba8;">⚠️ Parse Error</span>
            </div>
            <div class="step-thought">Retrying...</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Tool icon mapping
        icons = {
            "analyze_job": "🔍",
            "load_identity": "👤",
            "research_company": "🏢",
            "build_resume": "📝",
            "generate_pdf": "📄",
            "review_resume": "📋",
            "search_ddg": "🦆",
            "search_brave": "🦁",
        }
        icon = icons.get(action, "🔧")

        st.markdown(f"""
        <div class="step-card">
            <div class="step-header">
                <span class="step-number">Step {index}</span>
                <span class="step-action">{icon} {action}</span>
            </div>
            <div class="step-thought">💭 {thought}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show result in a collapsible
        result = step.get("result", {})
        if result:
            with st.expander(f"View {action} result", expanded=False):
                st.json(result)


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
    brave_enabled = st.toggle("🦁 Brave Search", value=True, help="Toggle Brave Search on/off")
    st.caption("Brave: Higher quality results (2,000 free/month)")
    st.caption("DuckDuckGo: Always available, unlimited, free")

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

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "agent":
        with st.chat_message("assistant", avatar="🤖"):
            if msg.get("steps"):
                for i, step in enumerate(msg["steps"], 1):
                    render_step(step, i)
            if msg.get("pdf_path"):
                st.success(f"📄 PDF generated: `{msg['pdf_path']}`")

# Chat input
goal = st.chat_input("What would you like me to do? (e.g., 'Tailor my resume for...')")

# Handle quick action presets
if quick_action == "Tailor my resume for a job" and not goal:
    st.info("💡 Paste a job description or URL in the chat box below, starting with: **Tailor my resume for this job:**")
elif quick_action == "Review my current CV" and not goal:
    st.info("💡 Paste a job description in the chat box, starting with: **Review my CV against this job:**")
elif quick_action == "Research a company" and not goal:
    st.info("💡 Type in the chat box: **Research [company name] and tell me about them**")

# Process new input
if goal:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": goal})

    with st.chat_message("user"):
        st.write(goal)

    # Run the agent
    with st.chat_message("assistant", avatar="🤖"):
        if not backend_online:
            st.error("Backend is offline. Start it first!")
        else:
            config = {"brave_search": brave_enabled}

            with st.spinner("🤖 Agent is thinking..."):
                try:
                    result = run_agent(goal, config)

                    steps = result.get("steps", [])
                    summary = result.get("final_summary", "")
                    pdf_path = result.get("pdf_path")

                    # Render each step
                    for i, step in enumerate(steps, 1):
                        render_step(step, i)

                    # PDF download button
                    if pdf_path:
                        st.success(f"📄 PDF generated: `{pdf_path}`")

                    # Save to session state
                    st.session_state.messages.append({
                        "role": "agent",
                        "content": summary,
                        "steps": steps,
                        "pdf_path": pdf_path,
                    })

                except requests.exceptions.Timeout:
                    st.error("⏱️ The agent took too long to respond. The local model might be slow on this task. Try a simpler goal.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
