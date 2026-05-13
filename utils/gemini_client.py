"""
gemini_client.py
Wrapper for Google Gemini API using the new google-genai SDK with retry logic.
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Use gemini-2.0-flash-lite — highest free-tier RPM quota
MODEL = "gemini-2.5-flash"


def _get_client():
    """Initialize Gemini client from API key."""
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _call_with_retry(prompt: str, retries: int = 3, delay: int = 15) -> str:
    """Call Gemini with automatic retry on 429 rate limit errors."""
    client = _get_client()
    if client is None:
        return "⚠️ **Gemini API key not configured.** Add GEMINI_API_KEY to your .env file."

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return (
                    f"⚠️ **Rate limit reached** on Gemini free tier. "
                    f"Please wait 60 seconds and click 'Regenerate AI Insights'."
                )
            return f"⚠️ Commentary unavailable: {err}"
    return "⚠️ Failed after retries."


@st.cache_data(ttl=3600, show_spinner=False)
def generate_commentary(prompt: str) -> str:
    """
    Send prompt to Gemini and return the text response.
    Cached for 1 hour to avoid repeat API calls on re-render.
    """
    return _call_with_retry(prompt)


def generate_all_commentary(prompts: dict) -> dict:
    """
    Generate commentary for all KPIs sequentially.
    Adds a small delay between calls to respect rate limits.
    """
    results = {}
    for i, (kpi_name, prompt) in enumerate(prompts.items()):
        results[kpi_name] = generate_commentary(prompt)
        if i < len(prompts) - 1:
            time.sleep(3)  # 3s gap between calls
    return results


def clear_cache():
    """Clear the Streamlit cache to force fresh AI generation."""
    generate_commentary.clear()
