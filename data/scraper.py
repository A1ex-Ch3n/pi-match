import json
import time
from pathlib import Path

import requests

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.semanticscholar.org/graph/v1"
MIN_YEAR = 2023  # papers from last 3 years (relative to 2026)

_RETRY_WAIT = 5  # seconds to wait on 429


def _get(url: str, params: dict = None) -> dict:
    """HTTP GET with rate-limit retry."""
    time.sleep(1)  # stay under 1 req/sec unauthenticated limit
    for attempt in range(3):
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 429:
            wait = _RETRY_WAIT * (attempt + 1)
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Failed after retries: {url}")


def _search_cache_path(slug: str) -> Path:
    return CACHE_DIR / f"search_{slug}.json"


def fetch_semantic_scholar(pi_name: str, institution: str) -> dict:
    """
    Fetches PI author data, recent papers (MIN_YEAR+), and co-authors
    from Semantic Scholar. Caches all responses under data/cache/.

    Returns a dict with:
        author_id, name, affiliations, recent_papers (list),
        co_author_ids (list), papers_last_12_months (int)
    """
    slug = pi_name.lower().replace(" ", "_")
    search_cache = _search_cache_path(slug)

    if search_cache.exists():
        with open(search_cache) as f:
            search_result = json.load(f)
    else:
        search_result = _get(
            f"{BASE_URL}/author/search",
            params={"query": pi_name, "fields": "authorId,name,affiliations"},
        )
        with open(search_cache, "w") as f:
            json.dump(search_result, f, indent=2)

    authors = search_result.get("data", [])
    if not authors:
        return {"error": f"No Semantic Scholar author found for '{pi_name}'"}

    # Best match: first result (SS ranks by citation count)
    author = authors[0]
    author_id = author["authorId"]

    profile_cache = CACHE_DIR / f"{author_id}.json"
    if profile_cache.exists():
        with open(profile_cache) as f:
            return json.load(f)

    # Fetch papers
    papers_data = _get(
        f"{BASE_URL}/author/{author_id}/papers",
        params={"fields": "title,abstract,year,authors", "limit": 50},
    )

    all_papers = papers_data.get("data", [])
    recent_papers = [
        p for p in all_papers
        if p.get("year") and p["year"] >= MIN_YEAR and p.get("abstract")
    ]

    current_year = 2026
    papers_last_12_months = sum(
        1 for p in all_papers if p.get("year") == current_year
    )

    # Extract co-author IDs from recent papers (skip the PI themselves)
    co_author_ids = []
    seen = set()
    for p in recent_papers:
        for a in p.get("authors", []):
            aid = a.get("authorId")
            if aid and aid != author_id and aid not in seen:
                co_author_ids.append(aid)
                seen.add(aid)

    # Deduplicate and cap
    co_author_ids = list(dict.fromkeys(co_author_ids))[:50]

    result = {
        "author_id": author_id,
        "name": author["name"],
        "affiliations": author.get("affiliations", []),
        "recent_papers": recent_papers[:20],
        "co_author_ids": co_author_ids,
        "papers_last_12_months": papers_last_12_months,
    }

    with open(profile_cache, "w") as f:
        json.dump(result, f, indent=2)

    return result


def resolve_author_name(author_id: str) -> str | None:
    """
    Looks up an author's name by SS ID. Used for co-author name resolution
    during indirect connection detection. Caches to data/cache/author_{id}.json.
    """
    cache_path = CACHE_DIR / f"author_{author_id}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        return data.get("name")

    try:
        data = _get(
            f"{BASE_URL}/author/{author_id}",
            params={"fields": "name,affiliations"},
        )
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)
        return data.get("name")
    except Exception:
        return None


if __name__ == "__main__":
    # Quick smoke test against Lior Pachter at Caltech
    result = fetch_semantic_scholar("Lior Pachter", "Caltech")
    print(f"Author: {result.get('name')} (ID: {result.get('author_id')})")
    print(f"Recent papers ({MIN_YEAR}+): {len(result.get('recent_papers', []))}")
    print(f"Co-authors found: {len(result.get('co_author_ids', []))}")
    if result.get("recent_papers"):
        print("First recent paper:", result["recent_papers"][0]["title"])
