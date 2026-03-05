import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))

def build(job_data: dict, identity_data: dict) -> dict:
    """
    Takes the analyzed job and your full identity profile.
    Returns a tailored resume as a structured dictionary.
    """

    prompt = f"""
    You are an expert resume writer and career coach.

    Your task is to create a tailored resume for the candidate below,
    specifically targeting the job description provided.

    ## CANDIDATE PROFILE
    Name: {identity_data["personal"]["name"]}
    Location: {identity_data["personal"]["location"]}
    Email: {identity_data["personal"]["email"]}
    Phone: {identity_data["personal"]["phone"]}
    LinkedIn: {identity_data["personal"]["linkedin"]}
    GitHub: {identity_data["personal"]["github"]}
    Portfolio: {identity_data["personal"]["portfolio"]}

    Default Summary: {identity_data["summary"]["default"]}

    Skills: {identity_data["skills"]}

    Extra Context: {identity_data["extra_context"]}

    Resume Text (from their actual CV):
    {identity_data["pdf_resume_text"]}

    GitHub Projects:
    {json.dumps(identity_data["github"]["repos"], indent=2)}

    Portfolio:
    {identity_data["portfolio"]["raw_text"]}

    ---

    ## TARGET JOB
    Title: {job_data["job_title"]}
    Company: {job_data["company_name"]}
    Location: {job_data["location"]}
    Required Skills: {job_data["required_skills"]}
    Nice to Have: {job_data["nice_to_have_skills"]}
    Responsibilities: {job_data["responsibilities"]}
    Tone: {job_data["tone"]}
    Summary: {job_data["summary"]}

    ---

    ## YOUR INSTRUCTIONS
    1. Write a tailored professional summary (3-4 sentences) that speaks directly to this job
    2. Select and reorder skills that are most relevant to this job — put the most relevant first
    3. Tailor work experience bullet points to highlight what matters for THIS job
    4. Select the most relevant projects from GitHub and portfolio
    5. Keep everything truthful — do NOT invent experience or skills
    6. Match the tone of the job description ({job_data["tone"]})

    Return ONLY a valid JSON object, no extra text:

    {{
        "personal": {{
            "name": "...",
            "email": "...",
            "phone": "...",
            "location": "...",
            "linkedin": "...",
            "github": "...",
            "portfolio": "..."
        }},
        "summary": "tailored 3-4 sentence summary here",
        "skills": ["most relevant first", "..."],
        "experience": [
            {{
                "company": "...",
                "role": "...",
                "duration": "...",
                "location": "...",
                "bullets": ["tailored bullet 1", "tailored bullet 2"]
            }}
        ],
        "projects": [
            {{
                "name": "...",
                "description": "...",
                "tech_stack": ["...", "..."],
                "url": "..."
            }}
        ],
        "education": [
            {{
                "institution": "...",
                "degree": "...",
                "duration": "...",
                "achievements": "..."
            }}
        ],
        "certifications": ["...", "..."]
    }}
    """
    response = model.generate_content(prompt)

    # Clean and parse the response
    raw_response = response.text.strip()

    if raw_response.startswith("```"):
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]

    return json.loads(raw_response)

def review(identity_data: dict, job_data: dict) -> dict:
    """
    Reviews the user's current CV against a job description.
    Returns section-by-section tips in plain text — no PDF.
    """

    prompt = f"""
    You are an expert career coach and CV reviewer.

    Review the candidate's current CV against the target job description below.
    Give specific, actionable tips for each section of THEIR CV.

    ## CANDIDATE'S CURRENT CV
    {identity_data["pdf_resume_text"]}

    ## TARGET JOB
    Title: {job_data["job_title"]}
    Company: {job_data["company_name"]}
    Required Skills: {job_data["required_skills"]}
    Responsibilities: {job_data["responsibilities"]}
    Tone: {job_data["tone"]}

    ## YOUR TASK
    Go through each section of their CV and give tips on:
    - What's working well
    - What to improve or reword
    - What's missing that the job requires
    - What to remove or deprioritize for THIS job

    Return ONLY a valid JSON object, no extra text:

    {{
        "overall_score": "X/10",
        "overall_summary": "2-3 sentence overall assessment",
        "sections": {{
            "introduction": {{
                "current": "quote or paraphrase their current summary",
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }},
            "experience": {{
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }},
            "technical_skills": {{
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }},
            "projects": {{
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }},
            "education": {{
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }},
            "certifications": {{
                "score": "X/10",
                "whats_working": "...",
                "tips": ["tip 1", "tip 2"]
            }}
        }},
        "missing_keywords": ["keyword 1", "keyword 2"],
        "quick_wins": ["easy change 1", "easy change 2", "easy change 3"]
    }}
    """

    response = model.generate_content(prompt)

    raw_response = response.text.strip()

    if raw_response.startswith("```"):
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]

    import json
    return json.loads(raw_response)