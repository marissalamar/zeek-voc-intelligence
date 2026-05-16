import requests
from datetime import datetime, timedelta, timezone
import time
import streamlit as st

GITHUB_API = "https://api.github.com"

def get_headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

import os

def scrape_repo_issues(repo: str, days_back: int = 180) -> list[dict]:
    """Scrape open and recently closed issues from a public GitHub repo."""
    since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    issues = []
    page = 1

    for state in ["open", "closed"]:
        page = 1
        while True:
            url = f"{GITHUB_API}/repos/{repo}/issues"
            params = {
                "state": state,
                "since": since_date,
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "direction": "desc"
            }
            try:
                resp = requests.get(url, params=params, headers=get_headers(), timeout=15)
                if resp.status_code == 403:
                    st.warning(f"Rate limited on {repo}. Waiting 60s...")
                    time.sleep(60)
                    continue
                if resp.status_code != 200:
                    st.warning(f"Error fetching {repo} page {page}: {resp.status_code}")
                    break

                data = resp.json()
                if not data:
                    break

                for issue in data:
                    # Skip pull requests (GitHub API returns PRs in issues endpoint)
                    if "pull_request" in issue:
                        continue

                    # Filter by date
                    created = issue.get("created_at", "")
                    if created < since_date:
                        break

                    issues.append({
                        "id": f"{repo}#{issue['number']}",
                        "repo": repo,
                        "number": issue["number"],
                        "title": issue.get("title", ""),
                        "body": (issue.get("body") or "")[:1500],  # Cap body length
                        "state": issue.get("state", "open"),
                        "labels": [l["name"] for l in issue.get("labels", [])],
                        "comments": issue.get("comments", 0),
                        "reactions": issue.get("reactions", {}).get("total_count", 0),
                        "created_at": created[:10],
                        "updated_at": (issue.get("updated_at") or "")[:10],
                        "url": issue.get("html_url", ""),
                        "author": issue.get("user", {}).get("login", "unknown"),
                    })

                # Check if we got a full page
                if len(data) < 100:
                    break
                page += 1
                time.sleep(0.3)  # Rate limit respect

            except requests.exceptions.RequestException as e:
                st.warning(f"Network error on {repo}: {e}")
                break

    return issues


def scrape_all_repos(repos: list[str], days_back: int = 180) -> list[dict]:
    """Scrape issues from multiple repos."""
    all_issues = []
    for repo in repos:
        with st.spinner(f"Fetching {repo}..."):
            repo_issues = scrape_repo_issues(repo, days_back=days_back)
            all_issues.extend(repo_issues)
            st.write(f"  ✓ {repo}: {len(repo_issues)} issues")
            time.sleep(0.5)
    return all_issues
