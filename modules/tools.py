"""
Tool Registry for Resume Tailor Agent.

Each tool wraps an existing module function and provides
metadata (name, description, parameters) so the agent LLM
can discover and decide which tools to call.
"""

from modules import job_analyzer, identity_loader, resume_builder, company_researcher, pdf_generator


# ─── Tool wrapper functions ──────────────────────────────
# These thin wrappers pull args from the shared state bag
# so the agent doesn't have to manage raw dicts itself.

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

    # Attach company research if available
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


# ─── Tool Registry ───────────────────────────────────────
# This is what the agent reads to know what tools exist.

TOOLS = [
    {
        "name": "analyze_job",
        "description": "Analyze a job posting. Accepts a URL to a job listing or raw job description text. Returns structured job data including title, company, skills, responsibilities, and tone. This should typically be the first tool called.",
        "parameters": {
            "job_input": "URL or raw text of the job description (required)"
        },
        "function": tool_analyze_job,
    },
    {
        "name": "load_identity",
        "description": "Load the user's full identity profile from all sources (YAML profile, PDF resume, GitHub repos, portfolio website). No parameters needed. Must be called before build_resume or review_resume.",
        "parameters": {},
        "function": tool_load_identity,
    },
    {
        "name": "research_company",
        "description": "Research the target company by scraping their website and summarizing what they do, their culture, and why they could be a good fit. Requires analyze_job to have been called first.",
        "parameters": {},
        "function": tool_research_company,
    },
    {
        "name": "build_resume",
        "description": "Build a tailored resume by combining the job analysis and user identity. Produces a structured resume with tailored summary, reordered skills, customized experience bullets, and relevant projects. Requires both analyze_job and load_identity to have been called first.",
        "parameters": {},
        "function": tool_build_resume,
    },
    {
        "name": "generate_pdf",
        "description": "Generate a professional PDF from the tailored resume. Requires build_resume to have been called first. Outputs the PDF to the output/ directory.",
        "parameters": {},
        "function": tool_generate_pdf,
    },
    {
        "name": "review_resume",
        "description": "Review the user's current CV against a target job description. Returns section-by-section scores, tips, missing keywords, and quick wins. Requires both analyze_job and load_identity to have been called first. Use this when the user wants feedback on their existing CV rather than generating a new one.",
        "parameters": {},
        "function": tool_review_resume,
    },
]


def get_tool_descriptions() -> str:
    """Format tool descriptions for the agent's system prompt."""
    lines = []
    for tool in TOOLS:
        params = ", ".join(f"{k}: {v}" for k, v in tool["parameters"].items()) if tool["parameters"] else "none"
        lines.append(f"- **{tool['name']}** — {tool['description']}\n  Parameters: {params}")
    return "\n".join(lines)


def get_tool_by_name(name: str):
    """Look up a tool by name. Returns the tool dict or None."""
    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    return None
