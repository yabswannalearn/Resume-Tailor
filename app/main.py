from fastapi import FastAPI
from app.routers import resume
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Resume Tailor",
    description="Generates tailored resumes based on job descriptions",
    version="1.0.0"
)

app.include_router(resume.router)

@app.get("/")
def root():
    return {"message": "AI Resume Tailor is running!"}