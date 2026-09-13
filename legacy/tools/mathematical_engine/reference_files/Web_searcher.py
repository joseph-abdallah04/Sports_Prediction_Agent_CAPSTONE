import json
import sys

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def search_nrl_news(query, max_results=5):
    """Return recent news hits from DuckDuckGo (live API, no fallbacks)."""
    print(f"Searching news for: '{query}'...")
    with DDGS() as ddgs:
        return list(
            ddgs.news(
                keywords=query,
                region="au-en",
                timelimit="w",
                max_results=max_results,
            )
        )


def fetch_article_text(url):
    """Scrape paragraph text from a news article URL."""
    print(f"Fetching article: {url}")
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
        tag.decompose()

    paragraphs = [
        p.get_text().strip()
        for p in soup.find_all("p")
        if len(p.get_text().strip()) > 40
    ]
    if not paragraphs:
        raise ValueError("No article body found on page (may be blocked or non-article URL).")

    return "\n\n".join(paragraphs)


if __name__ == "__main__":
    query = "NRL injury team news"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print("=" * 70)
    print("   NRL NEWS SEARCH (live DuckDuckGo + article fetch)   ")
    print("=" * 70)

    try:
        hits = search_nrl_news(query, max_results=5)
    except Exception as e:
        print(f"\n[!] Search failed: {e}")
        sys.exit(1)

    if not hits:
        print("\n[!] No results returned. Try a different query or run again later.")
        sys.exit(1)

    print(f"\n[+] Found {len(hits)} news result(s):\n")
    for i, hit in enumerate(hits, 1):
        print(f"  {i}. {hit.get('title')}")
        print(f"     Source: {hit.get('source')} | Date: {hit.get('date')}")
        print(f"     URL: {hit.get('url')}")
        print(f"     Snippet: {hit.get('body', '')[:200]}...\n")

    print(json.dumps(hits, indent=2))

    article_url = hits[0]["url"]
    print("\n" + "=" * 70)
    print(f"Fetching full text from top result: {article_url}")
    print("=" * 70)

    try:
        article_text = fetch_article_text(article_url)
    except Exception as e:
        print(f"\n[!] Could not extract article text: {e}")
        print("    Snippet from search is still real; try another URL from the list above.")
        sys.exit(1)

    print("\n--- Article excerpt (first 1200 chars) ---\n")
    print(article_text[:1200])
    if len(article_text) > 1200:
        print("\n... [truncated] ...")
