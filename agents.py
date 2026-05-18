import os
from langchain_groq import ChatGroq
from langchain_classic.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0.1
)

# ─── Agent 1: Problem Analyzer ───────────────────────────────────

def analyze_problem(problem: str) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a research problem analyzer.

Given this research problem or idea:
{problem}

Extract and return EXACTLY this structure:
1. DOMAIN: What field is this? (e.g. Computer Vision, NLP, Finance)
2. KEYWORDS: 5 search keywords separated by commas
3. SEARCH_QUERY_1: Best query for Semantic Scholar
4. SEARCH_QUERY_2: Alternative query for ArXiv
5. CORE_PROBLEM: One sentence summary of the core problem
6. WHAT_IS_NEEDED: What kind of solution is needed?

Be specific and technical.
""")
    chain = prompt | llm
    result = chain.invoke({"problem": problem})
    return {"analysis": result.content, "original_problem": problem}


# ─── Agent 2: Research Analyst ───────────────────────────────────

def analyze_papers(problem: str, papers: list) -> dict:
    papers_text = ""
    for i, p in enumerate(papers[:10], 1):
        papers_text += f"""
Paper {i}:
Title: {p['title']}
Authors: {p.get('authors', 'Unknown')}
Year: {p.get('year', 'Unknown')}
Abstract: {p.get('abstract', 'N/A')}
Citations: {p.get('citations', 0)}
Source: {p.get('source', '')}
URL: {p.get('url', '')}
---"""

    prompt = ChatPromptTemplate.from_template("""
You are a research analyst. Analyze these papers related to:
"{problem}"

PAPERS:
{papers}

Provide:

## WHAT HAS BEEN DONE
List the main approaches, methods, and findings from these papers.
For each major approach, note: method used, dataset, performance metric if mentioned.

## METHODOLOGY COMPARISON
Create a text table comparing:
| Paper | Method | Dataset | Key Result | Limitation |
Fill this for the top 5 most relevant papers.

## HOW THOROUGHLY COVERED
Rate from 1-10 how well this problem has been studied.
Explain why.

Be specific, technical, and cite paper titles.
""")
    chain = prompt | llm
    result = chain.invoke({"problem": problem, "papers": papers_text})
    return {"analysis": result.content}


# ─── Agent 3: Gap Detector ───────────────────────────────────────

def detect_gaps(problem: str, papers: list, analysis: str) -> dict:
    papers_text = "\n".join([
        f"- {p['title']} ({p.get('year', '?')}): {p.get('abstract', '')[:200]}"
        for p in papers[:10]
    ])

    prompt = ChatPromptTemplate.from_template("""
You are a research gap detection expert.

ORIGINAL PROBLEM: {problem}

EXISTING PAPERS:
{papers}

ANALYSIS OF EXISTING WORK:
{analysis}

Identify:

## RESEARCH GAPS
List 3-5 specific things that have NOT been done yet.
For each gap:
- Gap: [what is missing]
- Why it matters: [impact if solved]
- Difficulty: [Easy / Medium / Hard]
- Evidence: [which papers show this gap exists]

## CONTRADICTIONS IN LITERATURE
Are there papers that contradict each other?
What is unresolved?

## WEAKNESSES IN EXISTING WORK
What do existing methods fail at?
What datasets are missing?
What scenarios are untested?

Be very specific. This is for a serious researcher.
""")
    chain = prompt | llm
    result = chain.invoke({
        "problem": problem,
        "papers": papers_text,
        "analysis": analysis
    })
    return {"gaps": result.content}


# ─── Agent 4: Novelty Advisor ────────────────────────────────────

def advise_novelty(problem: str, gaps: str, similarity_results: list) -> dict:
    similarity_text = "\n".join([
        f"- {r['title']} ({r['year']}): {r['similarity']}% similar"
        for r in similarity_results[:5]
    ]) if similarity_results else "No close matches found."

    prompt = ChatPromptTemplate.from_template("""
You are a research novelty advisor helping researchers find publishable contributions.

ORIGINAL PROBLEM: {problem}

RESEARCH GAPS FOUND:
{gaps}

SIMILARITY TO EXISTING WORK:
{similarity}

Provide:

## NOVELTY ASSESSMENT
How novel is this research idea? (Score 1-10)
What makes it original?
What is the risk of being scooped?

## TOP 3 NOVEL CONTRIBUTION IDEAS
For each idea:
- Title: [Proposed contribution title]
- What it is: [One paragraph description]
- Builds on: [Which existing papers]
- What makes it new: [Exact novelty]
- Target venue: [Journal or conference name]
- Estimated difficulty: [Easy/Medium/Hard]
- Estimated time to complete: [months]

## RECOMMENDED NEXT STEPS
What should the researcher do first?
What data do they need?
What baseline should they implement first?

Be honest about difficulty. Don't oversell novelty.
""")
    chain = prompt | llm
    result = chain.invoke({
        "problem": problem,
        "gaps": gaps,
        "similarity": similarity_text
    })
    return {"novelty": result.content}


# ─── Agent 5: Literature Review Writer (on demand) ───────────────

def write_literature_review(problem: str, papers: list, analysis: str, gaps: str) -> str:
    papers_text = ""
    for i, p in enumerate(papers[:10], 1):
        papers_text += f"""
[{i}] {p['title']}
Authors: {p.get('authors', 'Unknown')}
Year: {p.get('year', 'Unknown')}
Abstract: {p.get('abstract', 'N/A')[:300]}
URL: {p.get('url', '')}
---"""

    prompt = ChatPromptTemplate.from_template("""
You are an academic writer. Write a formal literature review section for a research paper.

RESEARCH TOPIC: {problem}

PAPERS TO CITE:
{papers}

ANALYSIS OF FIELD:
{analysis}

IDENTIFIED GAPS:
{gaps}

Write a proper academic literature review with:

1. Opening paragraph: Introduce the field and why it matters
2. Thematic grouping: Group papers by approach/method
3. Critical analysis: Don't just summarize — compare and contrast
4. Gap paragraph: End with what is missing (leading to your research)

FORMAT:
- Academic tone
- Use in-text citations like [Author, Year]
- 600-800 words
- Ready to paste into a research paper

Write ONLY the literature review text. No headings like "Here is your review".
""")
    chain = prompt | llm
    result = chain.invoke({
        "problem": problem,
        "papers": papers_text,
        "analysis": analysis,
        "gaps": gaps
    })
    return result.content