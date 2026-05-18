import streamlit as st
from graph import run_research
from agents import write_literature_review

st.set_page_config(
    page_title="Research Gap Finder",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
.paper-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
}
.gap-card {
    background: #FFF7ED;
    border-left: 4px solid #F97316;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
}
.novelty-card {
    background: #F0FDF4;
    border-left: 4px solid #22C55E;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
}
.similarity-high {
    background: #FEF2F2;
    border-left: 4px solid #EF4444;
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 0 8px 8px 0;
}
.similarity-low {
    background: #F0FDF4;
    border-left: 4px solid #22C55E;
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 0 8px 8px 0;
}
.source-badge-ss {
    display: inline-block;
    background: #DBEAFE;
    color: #1E40AF;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
}
.source-badge-arxiv {
    display: inline-block;
    background: #FEF3C7;
    color: #92400E;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
}
.source-badge-crossref {
    display: inline-block;
    background: #F3E8FF;
    color: #6B21A8;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
}
.source-badge-web {
    display: inline-block;
    background: #DCFCE7;
    color: #166534;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
}
.status-badge {
    display: inline-block;
    background: #DBEAFE;
    color: #1E40AF;
    padding: 4px 12px;
    border-radius: 99px;
    font-size: 13px;
    margin: 4px 0;
}
.section-header {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #E5E7EB;
}
.stat-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "lit_review" not in st.session_state:
    st.session_state.lit_review = None
if "problem" not in st.session_state:
    st.session_state.problem = ""

# ─── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔬 Research Gap Finder")
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("1. Enter your research problem")
    st.markdown("2. AI searches 380M+ papers")
    st.markdown("3. Finds what exists and what doesn't")
    st.markdown("4. Suggests novel contributions")
    st.markdown("---")

    st.markdown("**Data Sources:**")
    st.markdown('<span class="source-badge-ss">Semantic Scholar</span> 200M+ papers', unsafe_allow_html=True)
    st.markdown('<span class="source-badge-arxiv">ArXiv</span> 2M+ CS/AI papers', unsafe_allow_html=True)
    st.markdown('<span class="source-badge-crossref">CrossRef</span> 150M+ with DOIs', unsafe_allow_html=True)
    st.markdown('<span class="source-badge-web">Web</span> Recent articles', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Powered by:**")
    st.markdown("- Groq Llama 3.3 70B")
    st.markdown("- LangGraph")

    if st.session_state.result:
        st.markdown("---")
        papers = st.session_state.result.get("papers", [])

        # Source breakdown
        sources = {}
        for p in papers:
            src = p.get("source", "Unknown")
            sources[src] = sources.get(src, 0) + 1

        st.markdown("**Papers Found:**")
        st.metric("Total", len(papers))
        for src, count in sources.items():
            st.markdown(f"- {src}: **{count}**")

        similarity = st.session_state.result.get("similarity", [])
        if similarity:
            top_sim = similarity[0]["similarity"]
            st.metric("Top Similarity", f"{top_sim}%")

        st.markdown("---")
        if st.button("New Search", use_container_width=True):
            st.session_state.result = None
            st.session_state.lit_review = None
            st.session_state.problem = ""
            st.rerun()

# ─── Main area ───────────────────────────────────────────────────
st.title("🔬 Research Gap Finder")
st.markdown("*Discover what exists, find what doesn't, publish what matters.*")
st.markdown("---")

problem = st.text_area(
    "Describe your research problem or idea:",
    placeholder="""Examples:
- Real-time crowd density estimation using egocentric cameras
- Detecting fake news in low-resource languages
- Improving RAG accuracy for technical documents
- Gold price forecasting during market crises""",
    height=120,
    value=st.session_state.problem
)

col1, col2 = st.columns([3, 1])
with col1:
    search_btn = st.button(
        "🔍 Find Research Gaps",
        type="primary",
        use_container_width=True
    )
with col2:
    st.markdown("*~60-90 seconds*")

# ─── Run research ─────────────────────────────────────────────────
if search_btn and problem.strip():
    st.session_state.problem = problem
    st.session_state.lit_review = None

    progress_bar = st.progress(0)
    status_text = st.empty()

    steps = [
        ("Analyzing your problem...", 15),
        ("Searching Semantic Scholar...", 30),
        ("Searching ArXiv...", 42),
        ("Searching CrossRef...", 54),
        ("Analyzing papers...", 66),
        ("Checking similarity...", 76),
        ("Detecting gaps...", 87),
        ("Advising on novelty...", 95),
    ]

    with st.spinner("Running research agents..."):
        import time
        for msg, pct in steps:
            status_text.markdown(
                f'<div class="status-badge">⚙️ {msg}</div>',
                unsafe_allow_html=True
            )
            progress_bar.progress(pct)
            time.sleep(0.3)

        result = run_research(problem)
        st.session_state.result = result

    progress_bar.progress(100)
    status_text.markdown(
        '<div class="status-badge">✅ Complete!</div>',
        unsafe_allow_html=True
    )
    st.rerun()

elif search_btn and not problem.strip():
    st.warning("Please enter a research problem first.")

# ─── Display results ──────────────────────────────────────────────
if st.session_state.result:
    result = st.session_state.result
    papers = result.get("papers", [])
    similarity = result.get("similarity", [])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Papers Found",
        "📊 Analysis",
        "🔍 Gaps",
        "💡 Novelty",
        "📝 Literature Review"
    ])

    # ── Tab 1: Papers ─────────────────────────────────────────────
    with tab1:
        st.markdown(
            f'<div class="section-header">📄 {len(papers)} Papers Found</div>',
            unsafe_allow_html=True
        )

        # Source breakdown stats
        sources = {}
        for p in papers:
            src = p.get("source", "Unknown")
            sources[src] = sources.get(src, 0) + 1

        cols = st.columns(len(sources))
        for i, (src, count) in enumerate(sources.items()):
            with cols[i]:
                st.metric(src, count)

        st.markdown("---")

        # Similarity overview
        if similarity:
            st.markdown("**Similarity to Your Idea:**")
            for s in similarity[:5]:
                color_class = "similarity-high" if s["similarity"] > 50 else "similarity-low"
                src = s.get("source", "")
                st.markdown(
                    f'<div class="{color_class}">'
                    f'<b>{s["similarity"]}% similar</b> — '
                    f'{s["title"]} ({s.get("year", "?")}) '
                    f'[{src}]'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown("---")

        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            source_options = ["All"] + list(set([
                p.get("source", "Unknown") for p in papers
            ]))
            selected_source = st.selectbox("Filter by source:", source_options)
        with col2:
            sort_by = st.selectbox(
                "Sort by:",
                ["Citations (high to low)", "Year (newest first)", "Relevance"]
            )

        # Filter
        filtered = papers if selected_source == "All" else [
            p for p in papers if p.get("source") == selected_source
        ]

        # Sort
        if sort_by == "Citations (high to low)":
            filtered = sorted(filtered, key=lambda x: x.get("citations", 0), reverse=True)
        elif sort_by == "Year (newest first)":
            filtered = sorted(
                filtered,
                key=lambda x: x.get("year") if x.get("year") else 0,
                reverse=True
            )

        # Display papers
        for p in filtered:
            source = p.get("source", "")
            badge_class = {
                "Semantic Scholar": "source-badge-ss",
                "ArXiv": "source-badge-arxiv",
                "CrossRef": "source-badge-crossref",
            }.get(source, "source-badge-web")

            with st.expander(
                f"📄 {p['title']} ({p.get('year', '?')}) — {p.get('citations', 0)} citations"
            ):
                st.markdown(
                    f'<span class="{badge_class}">{source}</span>',
                    unsafe_allow_html=True
                )
                st.markdown(f"**Authors:** {p.get('authors', 'Unknown')}")
                st.markdown(f"**Year:** {p.get('year', 'Unknown')}")
                st.markdown(f"**Citations:** {p.get('citations', 0)}")

                # Show journal for CrossRef papers
                if p.get("journal") and p.get("journal") != "Unknown journal":
                    st.markdown(f"**Journal:** {p.get('journal')}")

                st.markdown(f"**Abstract:** {p.get('abstract', 'N/A')}")

                if p.get("url"):
                    st.markdown(f"**Link:** [{p['url']}]({p['url']})")

    # ── Tab 2: Analysis ───────────────────────────────────────────
    with tab2:
        st.markdown(
            '<div class="section-header">📊 What Has Been Done</div>',
            unsafe_allow_html=True
        )
        st.markdown(result.get("paper_analysis", "No analysis available."))

    # ── Tab 3: Gaps ───────────────────────────────────────────────
    with tab3:
        st.markdown(
            '<div class="section-header">🔍 Research Gaps Found</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="gap-card">'
            'These are areas where no or insufficient research exists. '
            'Each gap is a potential publication opportunity.'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(result.get("gaps", "No gaps detected."))

    # ── Tab 4: Novelty ────────────────────────────────────────────
    with tab4:
        st.markdown(
            '<div class="section-header">💡 Novel Contribution Ideas</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="novelty-card">'
            'Specific, publishable contributions you can make '
            'based on the identified gaps.'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(result.get("novelty", "No novelty advice available."))

    # ── Tab 5: Literature Review ──────────────────────────────────
    with tab5:
        st.markdown(
            '<div class="section-header">📝 Literature Review Draft</div>',
            unsafe_allow_html=True
        )
        st.info(
            "Generates a formal academic literature review "
            "ready to paste into your research paper. "
            "Takes ~15 seconds."
        )

        if st.session_state.lit_review:
            st.markdown(st.session_state.lit_review)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download as .txt",
                    data=st.session_state.lit_review,
                    file_name="literature_review.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col2:
                if st.button(
                    "🔄 Regenerate",
                    use_container_width=True
                ):
                    st.session_state.lit_review = None
                    st.rerun()
        else:
            if st.button(
                "✍️ Generate Literature Review Draft",
                type="primary",
                use_container_width=True
            ):
                with st.spinner("Writing literature review..."):
                    lit_review = write_literature_review(
                        problem=st.session_state.problem,
                        papers=result.get("papers", []),
                        analysis=result.get("paper_analysis", ""),
                        gaps=result.get("gaps", "")
                    )
                    st.session_state.lit_review = lit_review
                st.rerun()

# ─── Empty state ──────────────────────────────────────────────────
if not st.session_state.result and not search_btn:
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        **📄 380M+ Papers**
        Searches Semantic Scholar, ArXiv, and CrossRef simultaneously.
        """)
    with col2:
        st.markdown("""
        **🔍 Gap Detection**
        Finds what has NOT been done yet in your research area.
        """)
    with col3:
        st.markdown("""
        **💡 Novelty Advice**
        Specific publishable contributions with target journals.
        """)
    with col4:
        st.markdown("""
        **📝 Literature Draft**
        Auto-generates academic literature review on demand.
        """)