"""
AI Provider Abstraction for Resume Tailor Agent.

PURPOSE:
Instead of every module calling Gemini directly, they all call
generate() from this module. This module reads AI_PROVIDER from
your .env and routes to the right backend:

    AI_PROVIDER=ollama   → runs locally on your machine (free!)
    AI_PROVIDER=gemini   → calls Google's API (costs money)

HOW IT WORKS:
1. On startup, we read AI_PROVIDER from .env
2. We initialize the correct backend (Ollama or Gemini)
3. Every module calls generate(prompt) and gets a string back
4. The module doesn't need to know WHICH provider is being used

WHY THIS PATTERN:
- Switch providers with one env variable change
- Test locally with Ollama, deploy with Gemini
- Easy to add more providers later (OpenAI, Claude, etc.)
"""

import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def generate(prompt: str) -> str:
    """
    Generate text from the configured AI provider.

    This is the ONLY function the rest of the codebase calls.
    It handles all the provider-specific logic internally.

    Args:
        prompt: The full prompt string to send to the AI

    Returns:
        The AI's response as a plain string
    """
    if AI_PROVIDER == "ollama":
        return _generate_ollama(prompt)
    elif AI_PROVIDER == "gemini":
        return _generate_gemini(prompt)
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER}. Use 'ollama' or 'gemini'.")


def _generate_ollama(prompt: str) -> str:
    """
    Call the local Ollama server.

    Ollama runs at http://localhost:11434 by default.
    The 'ollama' Python SDK handles the HTTP calls for us.

    For Qwen3's thinking mode, the model may include <think>...</think>
    tags in its response. We strip those out since we only want the
    final answer, not the internal reasoning chain.
    """
    import ollama

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response["message"]["content"].strip()

    # Qwen3 thinking mode: strip out <think>...</think> blocks
    # These contain the model's internal chain-of-thought reasoning
    # which we don't want in the actual output
    if "<think>" in text:
        import re
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    return text


def _generate_gemini(prompt: str) -> str:
    """
    Call Google's Gemini API.

    Uses the google-generativeai SDK, same as before.
    The API key and model name come from .env.
    """
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(GEMINI_MODEL)

    response = model.generate_content(prompt)
    return response.text.strip()


def get_provider_info() -> dict:
    """
    Return info about the current provider config.
    Useful for debugging and the /health endpoint.
    """
    return {
        "provider": AI_PROVIDER,
        "model": OLLAMA_MODEL if AI_PROVIDER == "ollama" else GEMINI_MODEL,
    }
