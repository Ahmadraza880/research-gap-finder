from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from tools import (
    search_semantic_scholar,
    search_arxiv,
    search_crossref,
    search_tavily,
    check_similarity
)
from agents import (
    analyze_problem,
    analyze_papers,
    detect_gaps,
    advise_novelty
)

# ─── State ───────────────────────────────────────────────────────

class ResearchState(TypedDict):
    problem: str
    analysis: str
    papers: List[Dict[str, Any]]
    web_results: List[Dict[str, Any]]
    paper_analysis: str
    gaps: str
    similarity: List[Dict[str, Any]]
    novelty: str
    status: str

# ─── Nodes ───────────────────────────────────────────────────────

def node_analyze_problem(state: ResearchState) -> ResearchState:
    print(">> Analyzing problem...")
    result = analyze_problem(state["problem"])
    return {**state, "analysis": result["analysis"], "status": "Analyzing problem..."}


def node_search_papers(state: ResearchState) -> ResearchState:
    print(">> Searching papers...")

    analysis = state["analysis"]
    problem = state["problem"]

    query1 = problem
    query2 = problem

    for line in analysis.split("\n"):
        if "SEARCH_QUERY_1:" in line:
            query1 = line.replace("SEARCH_QUERY_1:", "").strip()
        if "SEARCH_QUERY_2:" in line:
            query2 = line.replace("SEARCH_QUERY_2:", "").strip()

    semantic_papers = search_semantic_scholar(query1, limit=8)
    arxiv_papers = search_arxiv(query2, limit=8)
    crossref_papers = search_crossref(query1, limit=6)
    web_results = search_tavily(problem, limit=5)

    all_papers = semantic_papers + arxiv_papers + crossref_papers
    seen_titles = set()
    unique_papers = []
    for p in all_papers:
        title = p["title"].lower().strip()
        if title not in seen_titles and title != "no title":
            seen_titles.add(title)
            unique_papers.append(p)

    return {
        **state,
        "papers": unique_papers,
        "web_results": web_results,
        "status": f"Found {len(unique_papers)} papers..."
    }

def node_analyze_papers(state: ResearchState) -> ResearchState:
    print(">> Analyzing papers...")
    result = analyze_papers(state["problem"], state["papers"])
    return {
        **state,
        "paper_analysis": result["analysis"],
        "status": "Analyzing papers..."
    }


def node_check_similarity(state: ResearchState) -> ResearchState:
    print(">> Checking similarity...")
    similarity = check_similarity(state["problem"], state["papers"])
    return {
        **state,
        "similarity": similarity,
        "status": "Checking similarity..."
    }


def node_detect_gaps(state: ResearchState) -> ResearchState:
    print(">> Detecting gaps...")
    result = detect_gaps(
        state["problem"],
        state["papers"],
        state["paper_analysis"]
    )
    return {
        **state,
        "gaps": result["gaps"],
        "status": "Detecting gaps..."
    }


def node_advise_novelty(state: ResearchState) -> ResearchState:
    print(">> Advising on novelty...")
    result = advise_novelty(
        state["problem"],
        state["gaps"],
        state["similarity"]
    )
    return {
        **state,
        "novelty": result["novelty"],
        "status": "Complete"
    }

# ─── Build Graph ─────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("analyze_problem", node_analyze_problem)
    graph.add_node("search_papers", node_search_papers)
    graph.add_node("analyze_papers", node_analyze_papers)
    graph.add_node("check_similarity", node_check_similarity)
    graph.add_node("detect_gaps", node_detect_gaps)
    graph.add_node("advise_novelty", node_advise_novelty)

    # Add edges
    graph.set_entry_point("analyze_problem")
    graph.add_edge("analyze_problem", "search_papers")
    graph.add_edge("search_papers", "analyze_papers")
    graph.add_edge("analyze_papers", "check_similarity")
    graph.add_edge("check_similarity", "detect_gaps")
    graph.add_edge("detect_gaps", "advise_novelty")
    graph.add_edge("advise_novelty", END)

    return graph.compile()


def run_research(problem: str) -> ResearchState:
    graph = build_graph()

    initial_state = ResearchState(
        problem=problem,
        analysis="",
        papers=[],
        web_results=[],
        paper_analysis="",
        gaps="",
        similarity=[],
        novelty="",
        status="Starting..."
    )

    result = graph.invoke(initial_state)
    return result