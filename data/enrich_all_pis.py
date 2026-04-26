#!/usr/bin/env python3
"""
data/enrich_all_pis.py

Enriches PIs that have no Semantic Scholar ID by searching SS by name,
verifying the match via institution affiliation, then fetching papers and
abstracts. Updates the DB in-place.

This is the second-stage enrichment after enrich_abstracts.py (which only
handled PIs that already had an SS ID). This script covers the remaining ~979.

Verification: SS returns the highest-citation author matching the name. We
verify by checking that at least one keyword from the PI's institution name
appears in the returned author's affiliations. Unverified matches are logged
as MISMATCH and skipped unless --force is passed.

Usage:
    python3 data/enrich_all_pis.py              # enrich verified matches only
    python3 data/enrich_all_pis.py --dry-run    # preview, no DB writes
    python3 data/enrich_all_pis.py --limit 50   # process first N PIs
    python3 data/enrich_all_pis.py --force      # skip affiliation check
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "sqlite:///./backend/pimatch.db")

BASE_URL   = "https://api.semanticscholar.org/graph/v1"
CACHE_DIR  = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
MIN_YEAR   = 2021
CURRENT_YEAR = 2026


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _get(url: str, params: dict | None = None) -> dict | None:
    time.sleep(10.0)  # SS free tier: ~100 req/5min; 10s = 6 req/min to avoid bursting
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
            wait = 30 * (attempt + 1)
            print(f"  Rate limited — waiting {wait}s …")
            time.sleep(wait)
            continue
        print(f"  HTTP {r.status_code}")
        return None
    return None


# ── Affiliation verification ──────────────────────────────────────────────────

def _institution_tokens(institution: str) -> set[str]:
    """Extract meaningful keywords from an institution name for matching."""
    stop = {"university", "college", "institute", "of", "the", "and", "at",
            "state", "national", "polytechnic", "technology"}
    tokens = set()
    for word in re.split(r"[\s,/\-]+", institution.lower()):
        w = word.strip(".")
        if len(w) >= 4 and w not in stop:
            tokens.add(w)
    return tokens


def _affiliation_matches(affiliations: list[dict], institution: str) -> bool:
    """Return True if any affiliation string contains an institution keyword."""
    tokens = _institution_tokens(institution)
    if not tokens:
        return True  # can't verify, accept
    aff_text = " ".join(
        (a.get("name") or "") for a in affiliations
    ).lower()
    return any(t in aff_text for t in tokens)


def _name_matches(query: str, returned: str) -> bool:
    """Fallback when SS has no affiliation data: accept if last name matches
    AND first names share the same initial. Rejects pure-initial last names for
    common short surnames (Wu, Li, Wang…) to avoid false positives."""
    def _parts(name: str) -> list[str]:
        return re.sub(r"[^a-z\s]", "", name.lower()).split()

    q = _parts(query)
    r = _parts(returned)
    if not q or not r:
        return False

    q_last, r_last = q[-1], r[-1]
    if q_last != r_last:
        return False

    # Short common surnames (≤3 chars) are too ambiguous without affiliation
    if len(q_last) <= 3:
        return False

    q_first, r_first = q[0], r[0]
    # If returned first is only an initial, it must match query's first letter
    if len(r_first) == 1:
        return r_first == q_first[0]
    # Both full first names — first initials must agree
    return q_first[0] == r_first[0]


# ── Search + fetch ────────────────────────────────────────────────────────────

def search_author(pi_name: str) -> dict | None:
    """Search SS for an author by name; return the top result or None."""
    slug = pi_name.lower().replace(" ", "_")
    cache = CACHE_DIR / f"search_{slug}.json"
    if cache.exists():
        with open(cache) as f:
            data = json.load(f)
    else:
        data = _get(
            f"{BASE_URL}/author/search",
            params={"query": pi_name, "fields": "authorId,name,affiliations"},
        )
        if data is not None:
            with open(cache, "w") as f:
                json.dump(data, f, indent=2)
    if not data:
        return None
    authors = data.get("data", [])
    return authors[0] if authors else None


def fetch_papers(author_id: str) -> list[dict]:
    """Fetch papers (MIN_YEAR+) for a known SS author ID; cached."""
    cache = CACHE_DIR / f"papers_{author_id}.json"
    if cache.exists():
        with open(cache) as f:
            return json.load(f)
    data = _get(
        f"{BASE_URL}/author/{author_id}/papers",
        params={"fields": "title,abstract,year,authors,citationCount", "limit": 50},
    )
    if not data:
        return []
    papers = [p for p in data.get("data", []) if p.get("year") and p["year"] >= MIN_YEAR]
    with open(cache, "w") as f:
        json.dump(papers, f, indent=2)
    return papers


# ── Main ──────────────────────────────────────────────────────────────────────

def enrich(dry_run: bool = False, limit: int | None = None, force: bool = False) -> None:
    from sqlmodel import Session, select
    from backend.database import engine
    from backend.models import PIProfile

    with Session(engine) as session:
        all_pis = session.exec(select(PIProfile)).all()
        targets = [
            pi for pi in all_pis
            if not pi.semantic_scholar_id
        ]

    if limit:
        targets = targets[:limit]

    total = len(targets)
    print(f"PIs without Semantic Scholar ID: {total}")
    if dry_run:
        print("\nDry run — no DB writes. First 15 targets:")
        for pi in targets[:15]:
            print(f"  [{pi.id:5d}] {pi.name[:40]:40s}  [{pi.institution[:25]}]")
        return

    updated   = 0
    mismatch  = 0
    not_found = 0

    for i, pi in enumerate(targets, 1):
        print(f"[{i:4d}/{total}] {pi.name[:40]:40s} [{pi.institution[:22]}]", end="  ")

        author = search_author(pi.name)
        if not author:
            print("NOT FOUND in SS")
            not_found += 1
            continue

        author_id    = author["authorId"]
        author_name  = author.get("name", "")
        affiliations = author.get("affiliations", [])

        # Verification: affiliation check first; if SS has no affiliation data,
        # fall back to name-similarity (last name + first initial must agree).
        aff_text = ", ".join(a.get("name", "") for a in affiliations[:2]) or "no affiliation listed"
        if force:
            verified = True
        elif affiliations:
            verified = _affiliation_matches(affiliations, pi.institution)
        else:
            verified = _name_matches(pi.name, author_name)

        if not verified:
            print(f"MISMATCH → SS returned '{author_name}' [{aff_text}]")
            mismatch += 1
            continue

        papers = fetch_papers(author_id)
        abstracts = [p["abstract"] for p in papers if p.get("abstract")]
        paper_records = [
            {"title": p.get("title", ""), "year": p.get("year"), "citations": p.get("citationCount")}
            for p in papers
        ]
        co_ids: list[str] = []
        seen: set[str] = set()
        for p in papers:
            for a in p.get("authors", []):
                aid = a.get("authorId")
                if aid and aid != author_id and aid not in seen:
                    co_ids.append(aid)
                    seen.add(aid)
        co_ids = co_ids[:50]
        papers_12m = sum(1 for p in papers if p.get("year") == CURRENT_YEAR)

        print(f"✓ '{author_name}' [{aff_text[:30]}] → {len(abstracts)} abs, {len(paper_records)} papers")

        with Session(engine) as session:
            pi_db = session.get(PIProfile, pi.id)
            if pi_db:
                pi_db.semantic_scholar_id = author_id
                pi_db.recent_abstracts    = abstracts
                pi_db.papers              = paper_records
                pi_db.co_author_ids       = co_ids
                if papers_12m > (pi_db.papers_last_12_months or 0):
                    pi_db.papers_last_12_months = papers_12m
                session.commit()
                updated += 1

    print(f"\nDone. Updated: {updated}  |  Mismatch skipped: {mismatch}  |  Not found: {not_found}")

    with Session(engine) as session:
        all_pis   = session.exec(select(PIProfile)).all()
        has_abs   = sum(1 for p in all_pis if p.recent_abstracts)
        has_ss_id = sum(1 for p in all_pis if p.semantic_scholar_id)
        print(f"PIs with abstracts now: {has_abs} / {len(all_pis)}")
        print(f"PIs with SS ID now    : {has_ss_id} / {len(all_pis)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich PIs without Semantic Scholar ID")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=None)
    parser.add_argument("--force",   action="store_true",
                        help="Skip affiliation verification (risky for common names)")
    args = parser.parse_args()
    enrich(dry_run=args.dry_run, limit=args.limit, force=args.force)
