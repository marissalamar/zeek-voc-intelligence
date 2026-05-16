import anthropic
import json
import os
import time
from typing import Optional

CACHE_FILE = "cache/classified_issues.json"
THEMES = [
    "Performance & Scalability",
    "Installation & Setup",
    "Documentation",
    "Protocol Support",
    "Scripting & API",
    "Bug / Unexpected Behavior",
    "Feature Request",
    "Networking & Connectivity",
    "Security",
    "Package Management",
    "Logging & Output",
    "Integration & Compatibility",
]

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment.")
    return anthropic.Anthropic(api_key=api_key)

def load_cache() -> list[dict]:
    os.makedirs("cache", exist_ok=True)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return []

def save_cache(issues: list[dict]):
    os.makedirs("cache", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(issues, f, indent=2)

def classify_single(issue: dict, client) -> dict:
    """Classify one issue using Claude."""
    prompt = f"""You are a product intelligence analyst. Classify the following GitHub issue from the Zeek/Corelight open source ecosystem.

Issue Title: {issue['title']}
Issue Body: {issue['body'][:800]}
Labels: {', '.join(issue['labels']) if issue['labels'] else 'none'}
State: {issue['state']}
Comments: {issue['comments']}

Return ONLY a valid JSON object with exactly these fields:
{{
  "theme": "<one of: {', '.join(THEMES)}>",
  "sentiment": "<positive|neutral|negative>",
  "severity": "<low|medium|high>",
  "type": "<bug|feature_request|question|documentation|other>",
  "one_line": "<one sentence: what the user needs or what broke, written from the user perspective, max 120 chars>",
  "product_area": "<the specific technical area this touches, e.g. 'TCP stream reassembly', 'Zeek scripting API', 'package installer', etc.>"
}}

Severity guide:
- high: blocks core functionality, data loss, security issue, many users affected (high comments/reactions)
- medium: workaround exists, affects a subset of users
- low: minor inconvenience, edge case, cosmetic

Return ONLY the JSON. No preamble, no explanation."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Clean up any markdown fencing
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        classification = json.loads(text)
        return {**issue, **classification}
    except (json.JSONDecodeError, Exception) as e:
        # Return issue with defaults on failure
        return {
            **issue,
            "theme": "Bug / Unexpected Behavior",
            "sentiment": "neutral",
            "severity": "low",
            "type": "other",
            "one_line": issue["title"][:120],
            "product_area": "Unknown",
            "classification_error": str(e)
        }

def classify_issues(issues: list[dict], batch_size: int = 5) -> list[dict]:
    """Classify a list of issues with Claude, batched to manage rate limits."""
    import streamlit as st
    client = get_client()
    classified = []
    total = len(issues)

    progress = st.progress(0, text="Classifying issues...")
    for i, issue in enumerate(issues):
        result = classify_single(issue, client)
        classified.append(result)

        # Update progress
        progress.progress((i + 1) / total, text=f"Classifying {i+1}/{total}: {issue['title'][:60]}...")

        # Rate limit: small sleep every batch
        if (i + 1) % batch_size == 0:
            time.sleep(0.5)

    progress.empty()
    return classified
