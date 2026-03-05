import os
import yaml
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# File paths
PROFILE_PATH = "identity/profile.yaml"
RESUME_PATH = "identity/my_resume.pdf"


def load_yaml() -> dict:
    """Load the manual profile YAML file."""
    with open(PROFILE_PATH, "r") as f:
        return yaml.safe_load(f)


def load_pdf() -> str:
    """Extract all text from the PDF resume."""
    doc = fitz.open(RESUME_PATH)
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    return full_text.strip()


def load_github(github_url: str) -> dict:
    """Pull public GitHub data using the GitHub REST API."""
    username = github_url.rstrip("/").split("/")[-1]
    base_url = f"https://api.github.com/users/{username}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    profile = requests.get(base_url, headers=headers).json()
    repos_response = requests.get(f"{base_url}/repos", headers=headers, params={
        "sort": "updated",
        "per_page": 6
    }).json()

    repos = []
    for repo in repos_response:
        repos.append({
            "name": repo.get("name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "url": repo.get("html_url")
        })

    return {
        "username": username,
        "bio": profile.get("bio"),
        "public_repos": profile.get("public_repos"),
        "followers": profile.get("followers"),
        "repos": repos
    }


def load_portfolio(portfolio_url: str) -> dict:
    """
    Scrape the portfolio website and extract structured info.
    Returns projects, skills, experience, education, and certificates.
    """
    response = requests.get(portfolio_url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove junk we don't need
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    raw_text = soup.get_text(separator="\n", strip=True)

    # Return structured raw text — resume_builder will use this
    return {
        "url": portfolio_url,
        "raw_text": raw_text
    }


def load() -> dict:
    """
    Main function.
    Loads all 4 sources and merges into one profile dict.
    """
    yaml_data = load_yaml()
    pdf_text = load_pdf()
    github_data = load_github(yaml_data["personal"]["github"])
    portfolio_data = load_portfolio(yaml_data["personal"]["portfolio"])

    return {
        "personal": yaml_data.get("personal"),
        "summary": yaml_data.get("summary"),
        "skills": yaml_data.get("skills"),
        "extra_context": yaml_data.get("extra_context"),
        "pdf_resume_text": pdf_text,
        "github": github_data,
        "portfolio": portfolio_data
    }