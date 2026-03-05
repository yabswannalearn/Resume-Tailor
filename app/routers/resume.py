from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from modules import job_analyzer, identity_loader, resume_builder, company_researcher, pdf_generator

router = APIRouter(prefix="/resume", tags=["Resume"])


class JobInput(BaseModel):
    job_input: str


class JobData(BaseModel):
    job_title: str
    company_name: str
    location: str
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    responsibilities: List[str] = []
    qualifications: List[str] = []
    tone: str
    summary: str


class GenerateInput(BaseModel):
    job_data: JobData


@router.post("/analyze-job")
def analyze_job(body: JobInput):
    result = job_analyzer.analyze(body.job_input)
    return result


@router.get("/load-identity")
def load_identity():
    result = identity_loader.load()
    return result


@router.post("/research-company")
def research_company(body: GenerateInput):
    result = company_researcher.research(body.job_data.model_dump())
    return result


@router.post("/generate")
def generate_resume(body: GenerateInput):
    # Step 1: Load identity
    identity_data = identity_loader.load()

    # Step 2: Build tailored resume
    tailored_resume = resume_builder.build(body.job_data.model_dump(), identity_data)

    # Step 3: Research company
    company_summary = company_researcher.research(body.job_data.model_dump())
    tailored_resume["company_research"] = company_summary

    # Step 4: Generate PDF
    output_path = pdf_generator.generate(tailored_resume)

    # Step 5: Return the PDF file directly
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename="tailored_resume.pdf"
    )

@router.post("/review")
def review_cv(body: GenerateInput):
    # Load your current CV
    identity_data = identity_loader.load()

    # Get section-by-section tips
    tips = resume_builder.review(identity_data, body.job_data.model_dump())

    return tips


# ─── Agent Endpoint ───────────────────────────────────────
# This is the new "brain" endpoint. Instead of calling specific
# pipeline steps, you just tell the agent what you want in
# plain English, and it figures out the rest.

from modules import agent

class AgentInput(BaseModel):
    goal: str  # e.g. "Tailor my resume for this job posting: https://..."
    config: Optional[dict] = None  # e.g. {"brave_search": false} to disable Brave


@router.post("/agent")
def agent_endpoint(body: AgentInput):
    """
    Natural language agent endpoint.
    Give it a goal and the agent decides which tools to call,
    in what order, adapting based on results.

    Optional config to toggle tools from the frontend:
    {"goal": "...", "config": {"brave_search": false}}
    """
    result = agent.run(body.goal, config=body.config)
    return result