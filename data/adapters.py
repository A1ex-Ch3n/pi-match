"""
data/adapters.py

Transforms raw PI records from all_pis_east.json and all_pis_west.json into
the PIProfileSeedItem-compatible dict format expected by the seeding pipeline.

Two source formats are handled:
  east  — uses 'school'/'url' keys, no abstracts, all recruiting_status.tier=-1
  west  — uses 'institution'/'lab_website' keys, closer to target schema
"""

from __future__ import annotations

import datetime
import json
from typing import Optional


_EAST_SCHOOL_TO_STATE: dict[str, str] = {
    "Brown University": "RI",
    "Columbia University": "NY",
    "Cornell University": "NY",
    "Dartmouth College": "NH",
    "Harvard University": "MA",
    "MIT": "MA",
    "Massachusetts Institute of Technology": "MA",
    "Princeton University": "NJ",
    "University of Pennsylvania": "PA",
    "Yale University": "CT",
}

_RECRUITING_STATUSES = {
    "actively_recruiting",
    "quietly_recruiting",
    "likely_recruiting",
    "about_to_recruit",
}
_NOT_RECRUITING_STATUSES = {"not_seeking", "not_recruiting"}


def _papers_last_12_months(papers: list[dict]) -> int:
    cutoff = datetime.date.today().year - 1
    return sum(1 for p in papers if (p.get("year") or 0) >= cutoff)


def adapt_east_pi(raw: dict) -> dict:
    """Map one all_pis_east.json record to PIProfileSeedItem format."""
    rs = raw.get("recruiting_status") or {}
    rs_tier = rs.get("tier", -1)
    tier = rs_tier if rs_tier not in (-1, None) else 2

    papers = [
        {
            "title": p.get("title", ""),
            "year": p.get("year"),
            "citations": p.get("citations"),
        }
        for p in (raw.get("recent_top_papers") or [])
    ]

    return {
        "name": raw["name"],
        "institution": raw["school"],
        "department": raw.get("department", ""),
        "email": raw.get("email"),
        "lab_website": raw.get("url"),
        "semantic_scholar_id": raw.get("semantic_scholar_id"),
        "research_areas": raw.get("research_areas") or [],
        "recent_abstracts": [],
        "co_author_ids": [],
        "co_author_names": [],
        "papers_last_12_months": _papers_last_12_months(papers),
        "papers": papers,
        "nsf_grants": [],
        "has_active_nsf_grant": False,
        "total_active_funding_usd": raw.get("total_active_funding_usd"),
        "funding_citizen_restricted": False,
        "tier": tier,
        "location": _EAST_SCHOOL_TO_STATE.get(raw.get("school", ""), ""),
        "lab_size": 5,
        "is_recruiting": True,
        "pi_survey": None,
        "student_survey_responses": [],
        "reply_likelihood": "medium",
    }


def _derive_is_recruiting(raw: dict) -> bool:
    is_recruiting_raw = raw.get("is_recruiting")
    if is_recruiting_raw is not None:
        return bool(is_recruiting_raw)
    status = (raw.get("recruiting_status") or {}).get("status")
    if status in _RECRUITING_STATUSES:
        return True
    if status in _NOT_RECRUITING_STATUSES:
        return False
    return True


def adapt_west_pi(raw: dict) -> dict:
    """Map one all_pis_west.json record to PIProfileSeedItem format."""
    rl = raw.get("reply_likelihood")
    reply_likelihood = rl.lower() if isinstance(rl, str) else rl

    papers = [
        {
            "title": p.get("title", ""),
            "year": p.get("year"),
            "citations": p.get("citations"),
        }
        for p in (raw.get("recent_papers") or [])
    ]

    pi_survey = raw.get("pi_survey")
    if isinstance(pi_survey, dict) and all(v is None for v in pi_survey.values()):
        pi_survey = None

    return {
        "name": raw["name"],
        "institution": raw.get("institution", ""),
        "department": raw.get("department", ""),
        "email": raw.get("email"),
        "lab_website": raw.get("lab_website"),
        "semantic_scholar_id": raw.get("semantic_scholar_id"),
        "research_areas": raw.get("research_areas") or [],
        "recent_abstracts": raw.get("recent_abstracts") or [],
        "co_author_ids": raw.get("co_author_ids") or [],
        "co_author_names": [],
        "papers_last_12_months": raw.get("papers_last_12_months") or 0,
        "papers": papers,
        "nsf_grants": raw.get("nsf_grants") or [],
        "has_active_nsf_grant": raw.get("has_active_nsf_grant") or False,
        "total_active_funding_usd": raw.get("total_active_funding_usd"),
        "funding_citizen_restricted": raw.get("funding_citizen_restricted") or False,
        "tier": raw.get("tier") or 3,
        "location": raw.get("location") or "",
        "lab_size": raw.get("lab_size") or 5,
        "is_recruiting": _derive_is_recruiting(raw),
        "pi_survey": pi_survey,
        "student_survey_responses": raw.get("student_survey_responses") or [],
        "reply_likelihood": reply_likelihood,
    }


def detect_format(record: dict) -> str:
    """Return 'east' or 'west' based on record keys."""
    if "school" in record and "url" in record:
        return "east"
    if "institution" in record or "region" in record:
        return "west"
    raise ValueError(f"Cannot detect format from keys: {list(record.keys())[:8]}")


def load_and_adapt_file(filepath: str) -> list[dict]:
    """Load a JSON file of raw PI records and return adapted dicts."""
    with open(filepath, encoding="utf-8") as f:
        raw_list = json.load(f)
    if not raw_list:
        return []
    fmt = detect_format(raw_list[0])
    adapter = adapt_east_pi if fmt == "east" else adapt_west_pi
    result = []
    for raw in raw_list:
        try:
            result.append(adapter(raw))
        except Exception as exc:
            print(f"[adapters] Skipping '{raw.get('name', '?')}': {exc}")
    return result
