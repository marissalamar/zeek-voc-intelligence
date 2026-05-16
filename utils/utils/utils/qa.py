import anthropic
import json
import os

def answer_question(question: str, issues: list[dict]) -> str:
    """Answer a question about the classified issues using Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "API key not configured."

    client = anthropic.Anthropic(api_key=api_key)

    # Build a compact data summary for context
    # We don't send all 1800 issues — we send a structured summary + most relevant issues
    theme_counts = {}
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    type_counts = {}
    repo_counts = {}
    high_severity = []
    sample_issues = []

    for issue in issues:
        theme = issue.get("theme", "Unknown")
        severity = issue.get("severity", "low")
        itype = issue.get("type", "other")
        repo = issue.get("repo", "unknown")

        theme_counts[theme] = theme_counts.get(theme, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        type_counts[itype] = type_counts.get(itype, 0) + 1
        repo_counts[repo] = repo_counts.get(repo, 0) + 1

        if severity == "high":
            high_severity.append({
                "title": issue.get("title", ""),
                "one_line": issue.get("one_line", ""),
                "theme": theme,
                "repo": repo,
                "url": issue.get("url", ""),
                "comments": issue.get("comments", 0),
            })

    # Include a sample of issues for richer Q&A
    import random
    sample = random.sample(issues, min(150, len(issues)))
    for issue in sample:
        sample_issues.append({
            "title": issue.get("title", ""),
            "one_line": issue.get("one_line", ""),
            "theme": issue.get("theme", ""),
            "severity": issue.get("severity", ""),
            "type": issue.get("type", ""),
            "repo": issue.get("repo", ""),
            "sentiment": issue.get("sentiment", ""),
            "product_area": issue.get("product_area", ""),
            "comments": issue.get("comments", 0),
            "url": issue.get("url", ""),
        })

    context = f"""You are a product intelligence assistant helping a Product Manager analyze open source community feedback for the Zeek/Corelight ecosystem.

DATASET SUMMARY:
- Total issues analyzed: {len(issues)}
- Repos covered: {json.dumps(repo_counts)}
- Theme distribution: {json.dumps(dict(sorted(theme_counts.items(), key=lambda x: -x[1])))}
- Severity breakdown: {json.dumps(severity_counts)}
- Issue types: {json.dumps(type_counts)}

HIGH SEVERITY ISSUES ({len(high_severity)} total):
{json.dumps(high_severity[:30], indent=2)}

SAMPLE OF ISSUES (150 random for pattern recognition):
{json.dumps(sample_issues, indent=2)}

IMPORTANT GUIDELINES:
- You are helping a PM make informed decisions. Provide evidence, not conclusions.
- When referencing specific issues, include their title and note they can find the URL in the table below.
- Be specific about counts and percentages where relevant.
- If a question can't be answered from this data, say so clearly.
- Do not recommend specific product decisions — surface the signal, let the PM decide.
- Keep answers focused and scannable — use bullet points where helpful.
- This is open source community data, not internal customer data. Remind the PM of this limitation when relevant."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            messages=[
                {"role": "user", "content": f"{context}\n\nPM QUESTION: {question}"}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error getting answer: {str(e)}"
