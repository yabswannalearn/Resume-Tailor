import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))


def scrape_company_website(company_name: str) -> str:
    """
    Tries to find and scrape the company's website.
    Uses a Google search query to find it first.
    """
    try:
        # Search for the company website
        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+official+website"
        headers = {"User-Agent": "Mozilla/5.0"}

        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        # Try to grab the first result link
        first_result = soup.find("a", href=True)
        company_url = None

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "url?q=" in href and "google" not in href:
                company_url = href.split("url?q=")[1].split("&")[0]
                break

        if not company_url:
            return f"Could not find website for {company_name}"

        # Now scrape the actual company website
        company_response = requests.get(company_url, headers=headers, timeout=10)
        company_soup = BeautifulSoup(company_response.text, "html.parser")

        for tag in company_soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        return company_soup.get_text(separator="\n", strip=True)[:3000]  # limit text size

    except Exception as e:
        return f"Could not scrape company website: {str(e)}"


def research(job_data: dict) -> dict:
    """
    Main function.
    Takes job_data and returns a structured company summary.
    """

    company_name = job_data.get("company_name", "Unknown Company")
    location = job_data.get("location", "")
    job_title = job_data.get("job_title", "")

    # Step 1: Scrape company info
    company_text = scrape_company_website(company_name)

    # Step 2: Ask Gemini to summarize it
    prompt = f"""
    You are a company research assistant helping a job applicant prepare for an application.

    Based on the information below, create a helpful "Know Before You Apply" summary.

    Company Name: {company_name}
    Location: {location}
    Role Applying For: {job_title}

    Company Website Text:
    {company_text}

    Return a JSON object with this structure, no extra text:
    {{
        "company_name": "...",
        "industry": "...",
        "what_they_do": "2-3 sentence description of what the company does",
        "culture_and_values": "what kind of workplace culture do they seem to have",
        "why_good_fit": "1-2 sentences on why this company could be a good fit for the applicant",
        "good_to_know": ["interesting fact 1", "interesting fact 2", "interesting fact 3"]
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