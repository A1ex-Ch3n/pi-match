#!/usr/bin/env python3
"""
data/enrich_abstracts.py

Fetches Semantic Scholar abstracts for PIs that have a semantic_scholar_id
but no recent_abstracts in the database, then updates the DB in-place.

Uses the author_id directly (no name-search step) and caches every response
to data/cache/ so re-runs are instant for already-fetched PIs.

Usage:
    python3 data/enrich_abstracts.py             # enrich all 93 enrichable PIs
    python3 data/enrich_abstracts.py --dry-run   # preview only, no DB writes
    python3 data/enrich_abstracts.py --limit 10  # process first N PIs
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "sqlite:///./backend/pimatch.db")

BASE_URL = "https://api.semanticscholar.org/graph/v1"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Include papers from the past 5 years — wider window gives more abstracts
MIN_YEAR = 2021
CURRENT_YEAR = 2026


def _get(url: str, params: dict | None = None) -> dict | None:
    """HTTP GET with rate-limit retry. Returns None on 404 or persistent failure."""
    time.sleep(1.5)  # 1.5 s gap → well under 100 req / 5 min unauthenticated limit
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=20)
        except requests.RequestException as exc:
            print(f"  Network error: {exc}")
            return None
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            wait = 12 * (attempt + 1)
            print(f"  Rate limited — waiting {wait}s …")
            time.sleep(wait)
            continue
        print(f"  HTTP {r.status_code} for {url}")
        return None
    return None


def fetch_papers(author_id: str) -> list[dict]:
    """Return papers (year >= MIN_YEAR) for a known SS author ID, using cache."""
    cache_path = CACHE_DIR / f"papers_{author_id}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    data = _get(
        f"{BASE_URL}/author/{author_id}/papers",
        params={"fields": "title,abstract,year,authors,citationCount", "limit": 50},
    )
    if not data:
        return []

    papers = [
        p for p in data.get("data", [])
        if p.get("year") and p["year"] >= MIN_YEAR
    ]
    with open(cache_path, "w") as f:
        json.dump(papers, f, indent=2)
    return papers


def enrich(dry_run: bool = False, limit: int | None = None) -> None:
    from sqlmodel import Session, select
    from backend.database import engine
    from backend.models import PIProfile

    with Session(engine) as session:
        all_pis = session.exec(select(PIProfile)).all()
        enrichable = [
            pi for pi in all_pis
            if pi.semantic_scholar_id
            and not (pi.recent_abstracts or [])
        ]

    if limit:
        enrichable = enrichable[:limit]

    total = len(enrichable)
    print(f"Enrichable PIs (have ssid, no abstracts): {total}")

    if dry_run:
        print("\nDry run — no DB writes. First 15 PIs:")
        for pi in enrichable[:15]:
            print(f"  [{pi.id:5d}] {pi.name[:35]:35s}  ssid={pi.semantic_scholar_id}")
        return

    updated = skipped = 0
    for i, pi in enumerate(enrichable, 1):
        print(f"[{i:3d}/{total}] {pi.name[:40]:40s} ssid={pi.semantic_scholar_id}")
        papers = fetch_papers(pi.semantic_scholar_id)

        if not papers:
            print("         → no papers found")
            skipped += 1
            continue

        abstracts = [p["abstract"] for p in papers if p.get("abstract")]
        paper_records = [
            {
                "title": p.get("title", ""),
                "year": p.get("year"),
                "citations": p.get("citationCount"),
            }
            for p in papers
        ]

        # Co-author IDs from all fetched papers
        co_ids: list[str] = []
        seen: set[str] = set()
        for p in papers:
            for a in p.get("authors", []):
                aid = a.get("authorId")
                if aid and aid != pi.semantic_scholar_id and aid not in seen:
                    co_ids.append(aid)
                    seen.add(aid)
        co_ids = co_ids[:50]

        papers_12m = sum(1 for p in papers if p.get("year") == CURRENT_YEAR)

        print(f"         → {len(abstracts)} abstracts, "
              f"{len(paper_records)} papers, {len(co_ids)} co-authors")

        with Session(engine) as session:
            pi_db = session.get(PIProfile, pi.id)
            if pi_db:
                pi_db.recent_abstracts = abstracts
                pi_db.papers = paper_records
                pi_db.co_author_ids = co_ids
                if papers_12m > (pi_db.papers_last_12_months or 0):
                    pi_db.papers_last_12_months = papers_12m
                session.commit()
                updated += 1

    print(f"\nFinished. Updated: {updated}  |  Skipped (no data): {skipped}")

    # Summary stats
    with Session(engine) as session:
        all_pis = session.exec(select(PIProfile)).all()
        now_has_abs = sum(1 for p in all_pis if p.recent_abstracts)
        print(f"PIs with abstracts in DB: {now_has_abs} / {len(all_pis)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich PI abstracts from Semantic Scholar")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N PIs")
    args = parser.parse_args()
    enrich(dry_run=args.dry_run, limit=args.limit)
