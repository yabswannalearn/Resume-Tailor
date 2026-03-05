import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))


def fetch_job_from_url(url: str) -> str:
    """If user gives a URL, scrape the text from it."""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def analyze(job_input: str) -> dict:
    """
    Accepts either a URL or raw job description text.
    Returns a structured dict of the job details.
    """

    # Step 1: Get raw text
    if job_input.startswith("http"):
        raw_text = fetch_job_from_url(job_input)
    else:
        raw_text = job_input

    # Step 2: Build the prompt
    prompt = f"""
    You are a job description analyst.

    Extract the following from the job description below and return ONLY a valid JSON object, no extra text:

    {{
        "job_title": "...",
        "company_name": "...",
        "location": "...",
        "employment_type": "...",
        "experience_required": "...",
        "required_skills": ["...", "..."],
        "nice_to_have_skills": ["...", "..."],
        "responsibilities": ["...", "..."],
        "qualifications": ["...", "..."],
        "tone": "formal | casual | technical",
        "summary": "2-3 sentence summary of what this job is about"
    }}

    Job Description:
    {raw_text}
    """

    # Step 3: Call Gemini
    response = model.generate_content(prompt)

    # Step 4: Clean and parse JSON response
    raw_response = response.text.strip()

    if raw_response.startswith("```"):
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]

    return json.loads(raw_response)