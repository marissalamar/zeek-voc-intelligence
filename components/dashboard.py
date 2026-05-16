import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.qa import answer_question

SEVERITY_ORDER = ["high", "medium", "low"]
SEVERITY_COLORS = {
    "high": "#E8473F",
    "medium": "#F5A623",
    "low": "#4A9D6F",
}
SENTIMENT_COLORS = {
    "negative": "#E8473F",
    "neutral": "#8B9AAD",
    "positive": "#4A9D6F",
}

def render_kpi_cards(df: pd.DataFrame):
    total = len(df)
    high = len(df[df["severity"] == "high"])
    themes = df["theme"].nunique()
    repos = df["repo"].nunique()
    feature_requests = len(df[df["type"] == "feature_request"])
    bugs = len(df[df["type"] == "bug"])

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics = [
        (col1, "Total Issues", f"{total:,}", None),
        (col2, "High Severity", f"{high:,}", f"{high/total*100:.0f}% of total"),
        (col3, "Feature Requests", f"{feature_requests:,}", f"{feature_requests/total*100:.0f}% of total"),
        (col4, "Bugs", f"{bugs:,}", f"{bugs/total*100:.0f}% of total"),
        (col5, "Themes Detected", f"{themes}", None),
        (col6, "Repos Covered", f"{repos}", None),
    ]
    for col, label, value, delta in metrics:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                {f'<div class="kpi-delta">{delta}</div>' if delta else ''}
            </div>
            """, unsafe_allow_html=True)

def render_charts(df: pd.DataFrame):
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<p class="section-label">ISSUES BY THEME</p>', unsafe_allow_html=True)
        theme_df = df.groupby(["theme", "severity"]).size().reset_index(name="count")
        theme_totals = df.groupby("theme").size().reset_index(name="total").sort_values("total", ascending=True)
        theme_df = theme_df.merge(theme_totals[["theme"]], on="theme")

        fig = px.bar(
            theme_df,
            x="count",
            y="theme",
            color="severity",
            color_discrete_map=SEVERITY_COLORS,
            orientation="h",
            category_orders={"severity": SEVERITY_ORDER, "theme": theme_totals["theme"].tolist()},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="'DM Mono', monospace", size=11, color="#C8D6E5"),
            legend=dict(orientation="h", y=-0.15, x=0, font=dict(size=10)),
            margin=dict(l=0, r=10, t=10, b=30),
            height=380,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=""),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", title=""),
            bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<p class="section-label">SENTIMENT DISTRIBUTION</p>', unsafe_allow_html=True)
        sentiment_counts = df["sentiment"].value_counts()
        fig2 = go.Figure(data=[go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.65,
            marker=dict(colors=[SENTIMENT_COLORS.get(s, "#888") for s in sentiment_counts.index]),
            textinfo="label+percent",
            textfont=dict(family="'DM Mono', monospace", size=11, color="#C8D6E5"),
            hovertemplate="%{label}: %{value} issues<extra></extra>",
        )])
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=220,
            annotations=[dict(
                text=f"{len(df)}<br>issues",
                x=0.5, y=0.5,
                font=dict(family="'DM Mono', monospace", size=13, color="#C8D6E5"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<p class="section-label">BY REPOSITORY</p>', unsafe_allow_html=True)
        repo_counts = df["repo"].value_counts().reset_index()
        repo_counts.columns = ["repo", "count"]
        repo_counts["repo_short"] = repo_counts["repo"].str.split("/").str[-1]

        fig3 = px.bar(
            repo_counts,
            x="repo_short",
            y="count",
            color_discrete_sequence=["#2C7BE5"],
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="'DM Mono', monospace", size=11, color="#C8D6E5"),
            margin=dict(l=0, r=0, t=5, b=0),
            height=140,
            xaxis=dict(gridcolor="rgba(0,0,0,0)", title=""),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=""),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown('<p class="section-label">FILTER & EXPLORE</p>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        severity_filter = st.multiselect("Severity", options=["high", "medium", "low"], default=["high", "medium", "low"])
    with col2:
        theme_options = sorted(df["theme"].unique().tolist())
        theme_filter = st.multiselect("Theme", options=theme_options, default=theme_options)
    with col3:
        repo_options = sorted(df["repo"].unique().tolist())
        repo_filter = st.multiselect("Repository", options=repo_options, default=repo_options)
    with col4:
        type_options = sorted(df["type"].unique().tolist())
        type_filter = st.multiselect("Type", options=type_options, default=type_options)
    with col5:
        sentiment_filter = st.multiselect("Sentiment", options=["positive", "neutral", "negative"], default=["positive", "neutral", "negative"])

    filtered = df[
        df["severity"].isin(severity_filter) &
        df["theme"].isin(theme_filter) &
        df["repo"].isin(repo_filter) &
        df["type"].isin(type_filter) &
        df["sentiment"].isin(sentiment_filter)
    ]
    return filtered

def render_issue_table(df: pd.DataFrame):
    st.markdown(f'<p class="section-label">ISSUES — {len(df):,} RESULTS</p>', unsafe_allow_html=True)

    # Sort options
    sort_col, sort_dir_col, _ = st.columns([2, 2, 6])
    with sort_col:
        sort_by = st.selectbox("Sort by", ["severity", "comments", "created_at", "theme"], index=1, label_visibility="collapsed")
    with sort_dir_col:
        sort_dir = st.selectbox("Direction", ["High → Low", "Low → High"], label_visibility="collapsed")

    ascending = sort_dir == "Low → High"
    severity_map = {"high": 0, "medium": 1, "low": 2}

    display_df = df.copy()
    if sort_by == "severity":
        display_df["_sev_sort"] = display_df["severity"].map(severity_map)
        display_df = display_df.sort_values("_sev_sort", ascending=ascending)
    else:
        display_df = display_df.sort_values(sort_by, ascending=ascending)

    # Render as custom HTML table for full control
    rows_html = ""
    for _, row in display_df.head(200).iterrows():
        sev_class = f"sev-{row.get('severity', 'low')}"
        sent_class = f"sent-{row.get('sentiment', 'neutral')}"
        url = row.get("url", "")
        repo_short = row.get("repo", "").split("/")[-1]

        rows_html += f"""
        <tr>
            <td><span class="badge {sev_class}">{row.get('severity','').upper()}</span></td>
            <td><span class="badge-outline">{row.get('type','').replace('_',' ')}</span></td>
            <td class="issue-title">
                <a href="{url}" target="_blank" class="issue-link">{row.get('title','')[:80]}</a>
                <div class="issue-one-line">{row.get('one_line','')}</div>
            </td>
            <td class="theme-cell">{row.get('theme','')}</td>
            <td class="meta-cell">{repo_short}</td>
            <td class="meta-cell"><span class="{sent_class}">{row.get('sentiment','')}</span></td>
            <td class="meta-cell">{row.get('comments', 0)} 💬</td>
            <td class="meta-cell">{row.get('created_at','')[:10]}</td>
        </tr>"""

    table_html = f"""
    <div class="table-wrapper">
        <table class="issue-table">
            <thead>
                <tr>
                    <th>SEV</th>
                    <th>TYPE</th>
                    <th>ISSUE</th>
                    <th>THEME</th>
                    <th>REPO</th>
                    <th>SENTIMENT</th>
                    <th>COMMENTS</th>
                    <th>OPENED</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    if len(display_df) > 200:
        st.caption(f"Showing top 200 of {len(display_df)} results. Use filters to narrow.")

def render_qa(issues: list[dict]):
    st.markdown("---")
    st.markdown('<p class="section-label">ASK THE DATA</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="qa-subtext">Ask a question about what you're seeing. This surfaces signal — the interpretation is yours.
    <br><em>Note: responses draw from a sample of the dataset for speed and cost efficiency.</em></p>
    """, unsafe_allow_html=True)

    suggested = [
        "What are the most common pain points around installation?",
        "Which themes have the most high-severity issues?",
        "What feature requests appear most frequently?",
        "Are there patterns in what's frustrating enterprise users?",
        "Which product areas seem most neglected based on open issues?",
    ]

    st.markdown('<div class="suggested-questions">' +
        "".join([f'<span class="sq-chip" onclick="">{q}</span>' for q in suggested]) +
        '</div>', unsafe_allow_html=True)

    question = st.text_input(
        "Your question",
        placeholder="e.g. What are the biggest pain points around logging?",
        label_visibility="collapsed",
        key="qa_input"
    )

    if st.button("Ask →", type="primary", key="qa_btn"):
        if question:
            with st.spinner("Analyzing..."):
                answer = answer_question(question, issues)
            st.session_state.qa_history.insert(0, {"q": question, "a": answer})

    if st.session_state.get("qa_history"):
        for entry in st.session_state.qa_history[:5]:
            st.markdown(f"""
            <div class="qa-entry">
                <div class="qa-question">Q: {entry['q']}</div>
                <div class="qa-answer">{entry['a']}</div>
            </div>
            """, unsafe_allow_html=True)

def render_dashboard(issues: list[dict]):
    df = pd.DataFrame(issues)

    # Ensure required columns exist
    for col in ["severity", "theme", "sentiment", "type", "repo", "comments", "created_at", "url", "one_line"]:
        if col not in df.columns:
            df[col] = ""

    df["comments"] = pd.to_numeric(df["comments"], errors="coerce").fillna(0).astype(int)

    # Header
    st.markdown("""
    <div class="dashboard-header">
        <div class="dashboard-title">
            <span class="logo-hex">⬡</span>
            Zeek Community Intelligence
        </div>
        <div class="dashboard-subtitle">
            Open source VOC — architecture proof of concept &nbsp;·&nbsp; 
            Internal data would replace this with CS notes, Salesforce, PM call recordings
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI cards
    render_kpi_cards(df)

    st.markdown("---")

    # Charts
    render_charts(df)

    st.markdown("---")

    # Filters + table
    filtered_df = render_filters(df)
    render_issue_table(filtered_df)

    # Q&A layer
    render_qa(issues)
