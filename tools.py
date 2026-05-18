import requests
import arxiv
import os
import re
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── Semantic Scholar ────────────────────────────────────────────

def search_semantic_scholar(query, limit=10):
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,citationCount,url,externalIds"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        papers = []
        for p in data.get("data", []):
            papers.append({
                "title": p.get("title", "No title"),
                "authors": ", ".join([a["name"] for a in p.get("authors", [])[:3]]),
                "year": p.get("year", "Unknown"),
                "abstract": p.get("abstract", "No abstract available")[:500],
                "citations": p.get("citationCount", 0),
                "url": p.get("url", ""),
                "source": "Semantic Scholar"
            })
        return papers
    except Exception as e:
        print(f"Semantic Scholar error: {e}")
        return []

# ─── ArXiv ───────────────────────────────────────────────────────

def search_arxiv(query, limit=10):
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance
        )
        papers = []
        for p in client.results(search):
            papers.append({
                "title": p.title,
                "authors": ", ".join([a.name for a in p.authors[:3]]),
                "year": p.published.year,
                "abstract": p.summary[:500],
                "citations": 0,
                "url": p.entry_id,
                "source": "ArXiv"
            })
        return papers
    except Exception as e:
        print(f"ArXiv error: {e}")
        return []

# ─── CrossRef ────────────────────────────────────────────────────

def search_crossref(query, limit=8):
    try:
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": limit,
            "select": "title,author,published,DOI,is-referenced-by-count,container-title,abstract"
        }
        headers = {
            "User-Agent": "ResearchGapFinder/1.0 (research tool)"
        }
        response = requests.get(
            url, params=params, headers=headers, timeout=10
        )
        data = response.json()

        papers = []
        for p in data.get("message", {}).get("items", []):
            title = p.get("title", ["No title"])[0]
            authors = ", ".join([
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in p.get("author", [])[:3]
            ])
            year = p.get("published", {}).get(
                "date-parts", [[None]])[0][0]
            doi = p.get("DOI", "")
            citations = p.get("is-referenced-by-count", 0)
            journal = p.get("container-title", ["Unknown journal"])
            journal = journal[0] if journal else "Unknown"
            abstract = p.get("abstract", f"Published in: {journal}")
            abstract = re.sub(r'<[^>]+>', '', abstract)[:500]

            papers.append({
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "citations": citations,
                "url": f"https://doi.org/{doi}" if doi else "",
                "source": "CrossRef",
                "journal": journal
            })
        return papers
    except Exception as e:
        print(f"CrossRef error: {e}")
        return []

# ─── Tavily ──────────────────────────────────────────────────────

def search_tavily(query, limit=5):
    try:
        results = tavily.search(
            query=f"research papers {query}",
            max_results=limit
        )
        articles = []
        for r in results.get("results", []):
            articles.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:400],
                "source": "Web"
            })
        return articles
    except Exception as e:
        print(f"Tavily error: {e}")
        return []

# ─── Similarity checker ──────────────────────────────────────────

def compute_similarity(text1, text2):
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return round(len(intersection) / len(union) * 100, 1)

def check_similarity(user_idea, papers):
    results = []
    for p in papers:
        score = compute_similarity(
            user_idea,
            f"{p['title']} {p.get('abstract', '')}"
        )
        if score > 0:
            results.append({
                "title": p["title"],
                "similarity": score,
                "year": p.get("year", ""),
                "url": p.get("url", ""),
                "source": p.get("source", "")
            })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:5]