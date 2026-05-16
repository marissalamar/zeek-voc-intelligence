# zeek-voc-intelligence
# Zeek VOC Intelligence Dashboard

A PM decision-support tool that scrapes public GitHub issues from the Zeek/Corelight open source ecosystem, classifies them using Claude AI, and surfaces structured product intelligence through an interactive dashboard.

**This is an architecture proof of concept.** The same system, pointed at internal CS notes, Salesforce data, and PM call recordings, would produce actionable customer intelligence for Corelight's product team.

---

## What It Does

- Scrapes open + recently closed issues from multiple public Zeek/Corelight repos
- Classifies each issue: theme, sentiment, severity, type, product area
- Caches results so repeat runs only process new issues
- Displays a filterable, sortable PM dashboard with direct links to source issues
- Includes a conversational Q&A layer: ask questions about the data, get evidence-based answers

## Tech Stack

| | |
|---|---|
| Language | Python |
| AI | Claude (Anthropic) — claude-sonnet-4-5 |
| Scraping | GitHub REST API (public, no auth required) |
| Dashboard | Streamlit |
| Charts | Plotly |
| Hosting | Render.com |
| Cache | JSON (local file) |

## Setup

### 1. Clone and install

```bash
git clone <your-repo>
cd corelight-voc
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export ANTHROPIC_API_KEY=your_key_here
export GITHUB_TOKEN=your_github_token  # optional but recommended
```

### 3. Run locally

```bash
streamlit run app.py
```

### 4. Deploy to Render

1. Push to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add `ANTHROPIC_API_KEY` in Environment Variables

---

## How to Use

1. Select repositories in the sidebar
2. Choose time window (90 or 180 days)
3. Click **Refresh** to scrape + classify
4. Filter by severity, theme, repo, type, sentiment
5. Click any issue title to open it directly in GitHub
6. Use **Ask the Data** to query across all classified issues

---

## Cost

- First full run (~800–1500 issues): ~$2–5 in API credits
- Subsequent runs: nearly free — only new issues are classified
- Q&A queries: ~$0.01–0.03 per question

---

## Architecture

```
Public GitHub Issues          →  Internal CS Notes
                                  Salesforce Records
                                  PM Call Recordings
         ↓                              ↓
    GitHub REST API              Internal APIs / MCP
         ↓                              ↓
         ────────── Claude Classification ──────────
                            ↓
                    Cached + Structured Data
                            ↓
                    Streamlit Dashboard + Q&A
                            ↓
                    PM Decision + Human Judgment
```

The last step is not automated. That's the point.

---

*Built by Marissa Lamar — May 2026*
