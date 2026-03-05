from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse
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


# ─── Agent Endpoints ──────────────────────────────────────

from modules import agent

class AgentInput(BaseModel):
    goal: str
    config: Optional[dict] = None


@router.post("/agent")
def agent_endpoint(body: AgentInput):
    """Original non-streaming agent endpoint (returns all at once)."""
    result = agent.run(body.goal, config=body.config)
    return result


@router.post("/agent/stream")
def agent_stream_endpoint(body: AgentInput):
    """
    Streaming agent endpoint — sends steps in real-time via SSE.
    Each line is a JSON event the frontend can parse and display
    as the agent thinks.
    """
    return StreamingResponse(
        agent.run_streaming(body.goal, config=body.config),
        media_type="text/event-stream",
    )