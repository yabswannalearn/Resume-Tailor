from fastapi import APIRouter
from pydantic import BaseModel
from modules import job_analyzer, identity_loader

router = APIRouter(prefix="/resume", tags=["Resume"])

class JobInput(BaseModel):
    job_input: str

@router.post("/analyze-job")
def analyze_job(body: JobInput):
    result = job_analyzer.analyze(body.job_input)
    return result


@router.post("/generate")
def generate_resume():
    return {"message": "generate endpoint is working!"}

@router.get("/load-identity")
def load_identity():
    result = identity_loader.load()
    return result