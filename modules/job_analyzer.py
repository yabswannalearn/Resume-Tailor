"""
Job Analyzer Module.

PURPOSE:
Takes a job description (URL or raw text) and extracts structured data
from it — job title, company, skills, responsibilities, etc.

HOW IT WORKS:
1. If the input is a URL → scrape the page text with BeautifulSoup
2. Send the raw text to AI to clean/normalize it (format_job_text)
3. Send the cleaned text to AI to extract structured JSON (analyze)
4. Return a dict with all the job details

UPDATED: Now uses ai_provider.generate() instead of direct Gemini calls.
This means it works with both Ollama (local) and Gemini (cloud).
"""

import json
import requests
from bs4 import BeautifulSoup
from modules.ai_provider import generate


def fetch_job_from_url(url: str) -> str:
    """If user gives a URL, scrape the text from it."""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def format_job_text(raw_text: str) -> str:
    """
    Pre-processing agent.
    Takes messy raw job description text and normalizes it
    into clean, consistently structured plain text.
    """
    prompt = f"""
    You are a text formatting assistant.

    The text below is a raw job description. It may be messy, 
    have inconsistent spacing, broken formatting, or extra noise.

    Your job is to:
    1. Clean up the formatting and whitespace
    2. Keep ALL the original information — do not remove anything important
    3. Organize it into clear sections:
       - Job Title & Company
       - About the Company
       - About the Role
       - Responsibilities
       - Required Skills
       - Nice to Have
       - Benefits
    4. Output clean, readable plain text only
    5. Remove any duplicate or redundant lines

    Raw Job Description:
    {raw_text}

    Return only the cleaned text, no commentary.
    """

    return generate(prompt)


def analyze(job_input: str) -> dict:
    """
    Main function.
    Accepts either a URL or raw job description text.
    Returns a structured dict of the job details.
    """

    # Step 1: Get raw text
    if job_input.startswith("http"):
        raw_text = fetch_job_from_url(job_input)
    else:
        raw_text = job_input

    # Step 2: Clean and normalize the text first
    cleaned_text = format_job_text(raw_text)

    # Step 3: Build the analysis prompt using the CLEANED text
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
    {cleaned_text}
    """

    # Step 4: Call AI provider (Ollama or Gemini)
    raw_response = generate(prompt)

    # Step 5: Clean and parse JSON response
    if raw_response.startswith("```"):
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]

    return json.loads(raw_response)
