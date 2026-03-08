# 🤖 Resume Tailor Agent

An AI-powered agent that autonomously tailors resumes, reviews CVs, and researches companies — all through natural language. Just tell it what you need and it figures out the rest using a **ReAct reasoning loop**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)

---

## ✨ Features

- **🧠 Autonomous Agent** — Uses a ReAct (Think → Act → Observe) loop to plan and execute multi-step tasks on its own
- **📝 Resume Tailoring** — Generates ATS-optimized resumes customized to specific job descriptions
- **📋 CV Review** — Section-by-section scoring with actionable tips and missing keyword detection
- **🏢 Company Research** — Scrapes and summarizes company websites for culture fit analysis
- **📄 PDF Generation** — Produces clean, professional PDFs using ReportLab
- **🔍 Web Search** — Integrated Brave Search + DuckDuckGo for real-time company and market research
- **🧩 Multi-Source Identity** — Pulls your profile from YAML, PDF resume, GitHub API, and portfolio website
- **💾 Long-Term Memory** — MongoDB Atlas-backed session history so the agent remembers past interactions
- **⚡ Real-Time Streaming** — Watch the agent think and act step-by-step in the UI via SSE
- **🔄 Dual AI Providers** — Switch between local Ollama (free) and Google Gemini (cloud) with one env variable

---

## 🏗️ Architecture

```
┌─────────────────────┐         HTTP/SSE         ┌──────────────────────┐
│  Streamlit Frontend │ ◄──────────────────────► │   FastAPI Backend    │
│   (frontend.py)     │                          │   (app/main.py)      │
└─────────────────────┘                          └──────────┬───────────┘
                                                            │
                                              ┌─────────────▼───────────┐
                                              │   Agent Core (agent.py) │
                                              │   ReAct Loop (10 max)   │
                                              └──────────┬──────────────┘
                          ┌───────────────────┬──────────┼──────────┬───────────────────┐
                          │                   │          │          │                   │
                  ┌───────▼────┐  ┌───────────▼─┐  ┌────▼───┐  ┌──▼───────┐  ┌────────▼─────┐
                  │ Job        │  │ Identity     │  │ Resume │  │ Company  │  │ PDF          │
                  │ Analyzer   │  │ Loader       │  │ Builder│  │ Research │  │ Generator    │
                  └────────────┘  └─────────────┘  └────────┘  └──────────┘  └──────────────┘
                                                            │
                                              ┌─────────────▼───────────┐
                                              │  MongoDB Session Memory  │
                                              └─────────────────────────┘
```

---

## 🧠 How It Works

### The ReAct Reasoning Loop

Instead of a fixed pipeline, the agent uses a **ReAct (Reason + Act)** loop to dynamically decide what to do based on your goal. Here's what happens under the hood:

```
User goal: "Tailor my resume for this job: [URL]"
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  THINK: AI reads goal + available tools + past memory   │
│  → decides to call: analyze_job(url=...)                │
└─────────────────────────┬───────────────────────────────┘
                          │ ACT
                          ▼
              [ analyze_job executes ]
              [ stores data in state ]
                          │ OBSERVE
                          ▼
┌─────────────────────────────────────────────────────────┐
│  THINK: AI sees job analysis result                     │
│  → decides to call: load_identity()                     │
└─────────────────────────┬───────────────────────────────┘
                          │ ACT
                          ▼
              [ load_identity executes ]
              [ reads YAML + PDF + GitHub + portfolio ]
                          │ OBSERVE
                          ▼
         ... (continues calling tools as needed) ...
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  THINK: All data gathered, work is done                 │
│  → action: "final_answer"                               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              Session saved to MongoDB
              PDF saved to output/
```

The agent responds in structured JSON each iteration:
- **Tool call:** `{"action": "analyze_job", "args": {"url": "..."}, "thought": "why"}`
- **Final answer:** `{"action": "final_answer", "summary": "...", "thought": "why done"}`

A **shared `state` dictionary** is passed to every tool so they can read each other's results — for example, `build_resume` automatically reads `state["job_data"]` set by `analyze_job`.

The loop runs a maximum of **10 iterations** to prevent infinite loops.

### Available Tools

| Tool | What it does |
|---|---|
| `analyze_job` | Fetches a job URL or parses raw text to extract title, skills, requirements, and tone |
| `load_identity` | Loads your profile from `profile.yaml` + your PDF resume + GitHub API + portfolio site |
| `research_company` | Scrapes the company website and web search results to build a culture summary |
| `build_resume` | Generates a tailored resume using job data + your identity |
| `generate_pdf` | Renders the tailored resume to a professional PDF using ReportLab |
| `review_resume` | Reviews your CV section-by-section with a score and improvement tips |
| `search_ddg` | DuckDuckGo web search (free, no key needed) |
| `search_brave` | Brave Search API (higher quality, requires API key) |

---

## 📦 Project Structure

```
Resume-Tailor/
├── app/
│   ├── main.py              # FastAPI app entry point
│   └── routers/
│       └── resume.py        # API endpoints (REST + streaming)
├── modules/
│   ├── agent.py             # ReAct agent core (think → act → observe loop)
│   ├── ai_provider.py       # AI abstraction (Ollama / Gemini)
│   ├── tools.py             # Tool registry (8 tools the agent can call)
│   ├── job_analyzer.py      # Parse job postings from URLs or text
│   ├── identity_loader.py   # Load profile from YAML + PDF + GitHub + portfolio
│   ├── resume_builder.py    # Generate tailored resume content
│   ├── company_researcher.py # Scrape and summarize company websites
│   ├── pdf_generator.py     # Render resume to professional PDF (ReportLab)
│   ├── memory.py            # MongoDB-backed session memory
│   └── database.py          # MongoDB Atlas connection manager
├── identity/                # ⚠️ Not tracked by git — you create this
│   ├── profile.yaml         # Your personal profile data (see template below)
│   └── YourName CV.pdf      # Your current resume/CV
├── output/                  # Generated PDFs are saved here
├── frontend.py              # Streamlit chat UI
├── requirements.txt         # Python dependencies
└── .env                     # API keys and config (not tracked by git)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [MongoDB Atlas](https://www.mongodb.com/atlas) account (free tier works)
- *(Optional)* [Ollama](https://ollama.com/) installed for local AI
- *(Optional)* [Brave Search API](https://brave.com/search/api/) key (free tier: 2,000 queries/month)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/Resume-Tailor.git
cd Resume-Tailor
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure `.env`

Create a `.env` file in the project root:

```env
# AI Provider: "ollama" (free, local) or "gemini" (cloud)
AI_PROVIDER=gemini
OLLAMA_MODEL=qwen3:4b
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# MongoDB Atlas connection string
MONGODB_URI=your_mongodb_uri_here

# Brave Search (optional, free tier: 2000 queries/month)
BRAVE_API_KEY=your_brave_api_key_here
ENABLE_WEB_SEARCH=true
```

### 3. Set up your identity

Create an `identity/` folder and add your files:

```
identity/
├── profile.yaml      ← fill in your personal details (template below)
└── YourName CV.pdf   ← your current resume/CV as a PDF
```

> **Important:** Open `modules/identity_loader.py` and update the `RESUME_PATH` constant at the top to match your actual PDF filename.

#### `profile.yaml` template

```yaml
personal:
  name: "Your Full Name"
  email: "you@example.com"
  phone: "+1 (555) 000-0000"
  linkedin: "https://linkedin.com/in/yourhandle"
  github: "https://github.com/yourusername"
  portfolio: "https://yourportfolio.com"

summary: |
  A brief 2–3 sentence professional summary about yourself.
  Mention your domain, years of experience, and what you're looking for.

skills:
  - Python
  - FastAPI
  - React
  - SQL
  - Docker
  # add as many as you like

extra_context: |
  Any additional context you want the AI to know about you.
  For example: preferred job types, relocation preferences, salary range,
  notable projects not on your resume, etc.
```

### 4. Run

Open **two terminals**:

```bash
# Terminal 1: Start the backend
uvicorn app.main:app --reload
```

```bash
# Terminal 2: Start the frontend
streamlit run frontend.py
```

Visit **http://localhost:8501** and start chatting with the agent!

---

## 💬 Usage Examples

| Goal | What the agent does |
|---|---|
| *"Tailor my resume for this job: [URL]"* | Analyzes the job → loads your identity → researches the company → builds a tailored resume → generates a PDF |
| *"Review my CV against this job description"* | Scores each section, identifies missing keywords, suggests quick wins |
| *"Research Google and tell me about their engineering culture"* | Searches the web + scrapes the company site → returns a summary |

---

## ⚙️ Configuration

### AI Provider

Switch between providers by changing `AI_PROVIDER` in `.env`:

| Provider | Value | Cost | Notes |
|---|---|---|---|
| Ollama (local) | `ollama` | Free | Requires Ollama installed with a model pulled |
| Google Gemini | `gemini` | API pricing | Requires `GEMINI_API_KEY` |

### Web Search Toggle

The sidebar has a **🔍 Web Search** toggle that enables/disables both Brave and DuckDuckGo search tools. You can also set the default via `ENABLE_WEB_SEARCH` in `.env`.

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/resume/analyze-job` | Analyze a job posting |
| `GET` | `/resume/load-identity` | Load the user's profile |
| `POST` | `/resume/research-company` | Research a company |
| `POST` | `/resume/generate` | Full pipeline: generate a tailored resume PDF |
| `POST` | `/resume/review` | Review CV against a job description |
| `POST` | `/resume/agent` | Run the agent (returns all at once) |
| `POST` | `/resume/agent/stream` | Run the agent (streams steps via SSE) |

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `FileNotFoundError: identity/YourName CV.pdf` | Update `RESUME_PATH` in `modules/identity_loader.py` to match your PDF filename |
| `FileNotFoundError: identity/profile.yaml` | Create the `identity/` folder and add `profile.yaml` using the template above |
| Agent loops without finishing | The AI model may be too small — try `gemini-2.5-flash-lite` or a larger Ollama model |
| MongoDB connection error | Ensure `MONGODB_URI` in `.env` uses the correct Atlas connection string with password |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your activated virtual environment |
| Streamlit can't connect to backend | Make sure the FastAPI server is running on port 8000 before starting Streamlit |

---

## 📄 License

This project is for personal/educational use.

---

UI:
![alt text](/output/image.png)