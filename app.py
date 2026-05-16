import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Zeek VOC Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from utils.scraper import scrape_all_repos
from utils.classifier import classify_issues, load_cache, save_cache
from utils.qa import answer_question
from components.dashboard import render_dashboard

# ── Session state init ─────────────────────────────────────────────────────────
if "issues" not in st.session_state:
    st.session_state.issues = []
if "classified" not in st.session_state:
    st.session_state.classified = []
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []
if "loading" not in st.session_state:
    st.session_state.loading = False

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">⬡</div>
        <div class="sidebar-title">Zeek VOC<br><span>Intelligence Layer</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="sidebar-label">DATA SOURCES</p>', unsafe_allow_html=True)

    repos = {
        "zeek/zeek": st.checkbox("zeek/zeek — Core Platform", value=True),
        "zeek/zeek-docs": st.checkbox("zeek/zeek-docs — Documentation", value=True),
        "corelight/zeekjs": st.checkbox("corelight/zeekjs — JS Scripting", value=True),
        "zeek/package-manager": st.checkbox("zeek/package-manager — Ecosystem", value=True),
    }
    selected_repos = [r for r, checked in repos.items() if checked]

    st.markdown("---")
    st.markdown('<p class="sidebar-label">TIME WINDOW</p>', unsafe_allow_html=True)
    days_back = st.selectbox(
        "Issues from the last",
        options=[90, 120, 180],
        format_func=lambda x: f"{x} days",
        index=1
    )

    st.markdown("---")

    cache_exists = os.path.exists("cache/classified_issues.json")
    if cache_exists:
        with open("cache/classified_issues.json") as f:
            cached = json.load(f)
        st.markdown(f'<p class="sidebar-meta">Cache: {len(cached)} issues loaded</p>', unsafe_allow_html=True)
        try:
            ts = os.path.getmtime("cache/classified_issues.json")
            st.markdown(f'<p class="sidebar-meta">Last updated: {datetime.fromtimestamp(ts).strftime("%b %d, %Y")}</p>', unsafe_allow_html=True)
        except:
            pass

    col1, col2 = st.columns(2)
    with col1:
        refresh_btn = st.button("🔄 Refresh", use_container_width=True, type="primary")
    with col2:
        if cache_exists:
            load_btn = st.button("📂 Load Cache", use_container_width=True)
        else:
            load_btn = False

    st.markdown("---")
    st.markdown("""
    <div class="sidebar-about">
        <p class="sidebar-label">ABOUT THIS TOOL</p>
        <p class="sidebar-meta">This dashboard synthesizes public GitHub issues across Zeek/Corelight repositories into structured product intelligence. It is a decision-support tool — not a reporting tool. Human judgment is the final step.</p>
    </div>
    """, unsafe_allow_html=True)

# ── Data loading logic ─────────────────────────────────────────────────────────
if refresh_btn and selected_repos:
    with st.spinner("Scraping GitHub issues..."):
        raw_issues = scrape_all_repos(selected_repos, days_back=days_back)
    st.success(f"Fetched {len(raw_issues)} issues. Classifying with Claude...")

    existing_cache = load_cache()
    existing_ids = {i["id"] for i in existing_cache}
    new_issues = [i for i in raw_issues if i["id"] not in existing_ids]

    if new_issues:
        with st.spinner(f"Classifying {len(new_issues)} new issues with Claude AI..."):
            newly_classified = classify_issues(new_issues)
        all_classified = existing_cache + newly_classified
        save_cache(all_classified)
        st.session_state.classified = all_classified
        st.success(f"✓ Classified {len(new_issues)} new issues. {len(existing_cache)} loaded from cache.")
    else:
        st.session_state.classified = existing_cache
        st.info("No new issues found since last refresh. Loaded from cache.")

elif load_btn and cache_exists:
    st.session_state.classified = load_cache()
    st.success(f"Loaded {len(st.session_state.classified)} issues from cache.")

elif not st.session_state.classified and cache_exists:
    st.session_state.classified = load_cache()

# ── Main content ───────────────────────────────────────────────────────────────
if st.session_state.classified:
    render_dashboard(st.session_state.classified)
else:
    # Empty state
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">⬡</div>
        <h2>No data loaded yet</h2>
        <p>Select your repositories and click <strong>Refresh</strong> to scrape and classify GitHub issues,<br>
        or <strong>Load Cache</strong> if you've run this before.</p>
    </div>
    """, unsafe_allow_html=True)
