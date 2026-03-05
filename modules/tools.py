"""
Tool Registry for Resume Tailor Agent.

Each tool wraps an existing module function and provides
metadata (name, description, parameters) so the agent LLM
can discover and decide which tools to call.

TOOLS AVAILABLE:
- analyze_job: Parse a job posting into structured data
- load_identity: Load the user's profile from all sources
- research_company: Research a company's background
- build_resume: Generate a tailored resume
- generate_pdf: Render resume to PDF
- review_resume: Review CV against a job with tips
- search_ddg: Search the web via DuckDuckGo (free, no API key)
- search_brave: Search the web via Brave Search (free tier, needs API key)
"""

import os
from modules import job_analyzer, identity_loader, resume_builder, company_researcher, pdf_generator


# ─── Tool wrapper functions ──────────────────────────────

def tool_analyze_job(state: dict, args: dict) -> dict:
    """Analyze a job posting from URL or raw text."""
    job_input = args.get("job_input", "")
    result = job_analyzer.analyze(job_input)
    state["job_data"] = result
    return {"status": "success", "job_data": result}


def tool_load_identity(state: dict, args: dict) -> dict:
    """Load the user's full identity profile."""
    result = identity_loader.load()
    state["identity"] = result
    return {"status": "success", "identity_loaded": True, "name": result["personal"]["name"]}


def tool_research_company(state: dict, args: dict) -> dict:
    """Research the target company."""
    job_data = state.get("job_data")
    if not job_data:
        return {"status": "error", "message": "No job_data in state. Call analyze_job first."}
    result = company_researcher.research(job_data)
    state["company_research"] = result
    return {"status": "success", "company_research": result}


def tool_build_resume(state: dict, args: dict) -> dict:
    """Build a tailored resume from job data and identity."""
    job_data = state.get("job_data")
    identity = state.get("identity")
    if not job_data:
        return {"status": "error", "message": "No job_data in state. Call analyze_job first."}
    if not identity:
        return {"status": "error", "message": "No identity in state. Call load_identity first."}

    result = resume_builder.build(job_data, identity)

    if state.get("company_research"):
        result["company_research"] = state["company_research"]

    state["tailored_resume"] = result
    return {"status": "success", "resume_sections": list(result.keys())}


def tool_generate_pdf(state: dict, args: dict) -> dict:
    """Generate a PDF from the tailored resume."""
    resume = state.get("tailored_resume")
    if not resume:
        return {"status": "error", "message": "No tailored_resume in state. Call build_resume first."}
    output_path = pdf_generator.generate(resume)
    state["pdf_path"] = output_path
    return {"status": "success", "pdf_path": output_path}


def tool_review_resume(state: dict, args: dict) -> dict:
    """Review the user's current CV against a job description."""
    job_data = state.get("job_data")
    identity = state.get("identity")
    if not job_data:
        return {"status": "error", "message": "No job_data in state. Call analyze_job first."}
    if not identity:
        return {"status": "error", "message": "No identity in state. Call load_identity first."}
    result = resume_builder.review(identity, job_data)
    state["review"] = result
    return {"status": "success", "review": result}


def tool_search_ddg(state: dict, args: dict) -> dict:
    """
    Search the web using DuckDuckGo.
    Free, no API key needed. Good for general searches.
    """
    from duckduckgo_search import DDGS

    query = args.get("query", "")
    if not query:
        return {"status": "error", "message": "Missing 'query' parameter."}

    try:
        results = DDGS().text(query, max_results=5)
        formatted = [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
        state.setdefault("search_results", []).extend(formatted)
        return {"status": "success", "results": formatted}
    except Exception as e:
        return {"status": "error", "message": f"DuckDuckGo search failed: {str(e)}"}


def tool_search_brave(state: dict, args: dict) -> dict:
    """
    Search the web using Brave Search API.
    Requires a BRAVE_API_KEY in .env (free tier: 2,000 queries/month).
    Generally returns higher quality results than DuckDuckGo.
    """
    import requests

    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "BRAVE_API_KEY not set in .env. Get a free key at https://brave.com/search/api/"}

    query = args.get("query", "")
    if not query:
        return {"status": "error", "message": "Missing 'query' parameter."}

    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {"q": query, "count": 5}
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        formatted = []
        for r in data.get("web", {}).get("results", []):
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            })

        state.setdefault("search_results", []).extend(formatted)
        return {"status": "success", "results": formatted}
    except Exception as e:
        return {"status": "error", "message": f"Brave search failed: {str(e)}"}


# ─── Tool Registry ───────────────────────────────────────

TOOLS = [
    {
        "name": "analyze_job",
        "description": "Analyze a job posting. Accepts a URL to a job listing or raw job description text. Returns structured job data including title, company, skills, responsibilities, and tone. This should typically be the first tool called.",
        "parameters": {
            "job_input": "URL or raw text of the job description (required)"
        },
        "function": tool_analyze_job,
        "toggleable": False,
    },
    {
        "name": "load_identity",
        "description": "Load the user's full identity profile from all sources (YAML profile, PDF resume, GitHub repos, portfolio website). No parameters needed. Must be called before build_resume or review_resume.",
        "parameters": {},
        "function": tool_load_identity,
        "toggleable": False,
    },
    {
        "name": "research_company",
        "description": "Research the target company by scraping their website and summarizing what they do, their culture, and why they could be a good fit. Requires analyze_job to have been called first.",
        "parameters": {},
        "function": tool_research_company,
        "toggleable": False,
    },
    {
        "name": "build_resume",
        "description": "Build a tailored resume by combining the job analysis and user identity. Produces a structured resume with tailored summary, reordered skills, customized experience bullets, and relevant projects. Requires both analyze_job and load_identity to have been called first.",
        "parameters": {},
        "function": tool_build_resume,
        "toggleable": False,
    },
    {
        "name": "generate_pdf",
        "description": "Generate a professional PDF from the tailored resume. Requires build_resume to have been called first. Outputs the PDF to the output/ directory.",
        "parameters": {},
        "function": tool_generate_pdf,
        "toggleable": False,
    },
    {
        "name": "review_resume",
        "description": "Review the user's current CV against a target job description. Returns section-by-section scores, tips, missing keywords, and quick wins. Requires both analyze_job and load_identity to have been called first. Use this when the user wants feedback on their existing CV rather than generating a new one.",
        "parameters": {},
        "function": tool_review_resume,
        "toggleable": False,
    },
    {
        "name": "search_ddg",
        "description": "Search the web using DuckDuckGo. Free and requires no API key. Use this to look up company info, job market data, salary ranges, or any general information. Returns top 5 results with titles, URLs, and snippets.",
        "parameters": {
            "query": "The search query string (required)"
        },
        "function": tool_search_ddg,
        "toggleable": True,
        "toggle_key": "web_search",
    },
    {
        "name": "search_brave",
        "description": "Search the web using Brave Search. Higher quality results than DuckDuckGo but requires a BRAVE_API_KEY. Use this when you need more accurate or detailed search results. Returns top 5 results with titles, URLs, and snippets.",
        "parameters": {
            "query": "The search query string (required)"
        },
        "function": tool_search_brave,
        "toggleable": True,
        "toggle_key": "web_search",
    },
]


def get_active_tools(config: dict = None) -> list:
    """
    Return the list of currently active tools based on config.

    Config is a dict like {"brave_search": True/False}.
    If no config is passed, falls back to .env defaults.

    This is how the frontend will toggle tools on/off:
    - POST /resume/agent {"goal": "...", "config": {"brave_search": false}}
    """
    if config is None:
        config = {}

    # Default: check .env for ENABLE_WEB_SEARCH
    default_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"

    active = []
    for tool in TOOLS:
        if tool.get("toggleable") and tool.get("toggle_key"):
            key = tool["toggle_key"]
            enabled = config.get(key, default_web_search)
            if not enabled:
                continue

        active.append(tool)

    return active


def get_tool_descriptions(config: dict = None) -> str:
    """Format tool descriptions for the agent's system prompt."""
    lines = []
    for tool in get_active_tools(config):
        params = ", ".join(f"{k}: {v}" for k, v in tool["parameters"].items()) if tool["parameters"] else "none"
        lines.append(f"- **{tool['name']}** — {tool['description']}\n  Parameters: {params}")
    return "\n".join(lines)


def get_tool_by_name(name: str, config: dict = None):
    """Look up a tool by name from active tools. Returns the tool dict or None."""
    for tool in get_active_tools(config):
        if tool["name"] == name:
            return tool
    return None
