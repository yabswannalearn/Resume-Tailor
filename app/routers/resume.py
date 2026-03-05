from fastapi import APIRouter
from pydantic import BaseModel
from modules import job_analyzer, identity_loader, resume_builder

router = APIRouter(prefix="/resume", tags=["Resume"])

class JobInput(BaseModel):
    job_input: str

@router.post("/analyze-job")
def analyze_job(body: JobInput):
    result = job_analyzer.analyze(body.job_input)
    return result


@router.post("/generate")
def generate_resume(body: JobInput):
    #analyze
    job_data = job_analyzer.analyze(body.job_input)
    #load identity
    identity_data = identity_loader.load()
    #build the resume
    tailored_resume = resume_builder.build(job_data, identity_data)

    return tailored_resume

@router.get("/load-identity")
def load_identity():
    result = identity_loader.load()
    return result