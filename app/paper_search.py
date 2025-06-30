import requests
from bs4 import BeautifulSoup
import xmltodict

def search_arxiv(query, max_results=5):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    response = requests.get(url)
    data = xmltodict.parse(response.text)
    entries = data.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):  # only one result
        entries = [entries]
    return [
        {
            "title": e["title"].strip(),
            "summary": e.get("summary", "").strip(),
            "url": e.get("id", "")
        }
        for e in entries
    ]

def search_semantic_scholar(query, max_results=5):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,url,abstract"
    r = requests.get(url)
    data = r.json()
    return [
        {
            "title": p["title"],
            "summary": p.get("abstract", "No abstract found."),
            "url": p.get("url", "")
        }
        for p in data.get("data", [])
    ]

def search_core(query, max_results=5):
    # CORE Search API via their site search
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://core.ac.uk/search?q={query}&page=1"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.select(".result-title a")[:max_results]
    return [
        {
            "title": r.text.strip(),
            "summary": "No summary available.",
            "url": "https://core.ac.uk" + r.get("href")
        }
        for r in results
    ]

def search_pubmed(query, max_results=5):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
    ids = requests.get(url).json().get("esearchresult", {}).get("idlist", [])
    summaries = []
    for pmid in ids:
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        res = requests.get(summary_url).json()
        doc = res.get("result", {}).get(pmid, {})
        summaries.append({
            "title": doc.get("title", "No title"),
            "summary": doc.get("source", "PubMed entry"),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
    return summaries

def search_all_sources(query, max_results=5):
    return {
        "arxiv": search_arxiv(query, max_results),
        "semantic_scholar": search_semantic_scholar(query, max_results),
        "core": search_core(query, max_results),
        "pubmed": search_pubmed(query, max_results),
    }
