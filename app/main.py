from fastapi import FastAPI
from app.routers import resume
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Resume Tailor Agent",
    description="An AI agent that autonomously tailors resumes, reviews CVs, and researches companies through natural language goals",
    version="2.0.0"
)

app.include_router(resume.router)

@app.get("/")
def root():
    return {"message": "AI Resume Tailor is running!"}