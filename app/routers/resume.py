from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from modules import job_analyzer, identity_loader, resume_builder, company_researcher

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

    # Step 3: Research the company
    company_summary = company_researcher.research(body.job_data.model_dump())

    # Step 4: Attach company summary to the resume output
    tailored_resume["company_research"] = company_summary

    return tailored_resume