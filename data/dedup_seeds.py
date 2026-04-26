"""
data/dedup_seeds.py

Pre-seeding normalisation step: called by _auto_seed_pis() and POST /api/pi/seed
before any rows are written to the database.

Three responsibilities:
  1. Filter — drop entries whose name is blank, "Unknown", or "Unknown PI".
  2. Normalise — strip lab-name suffixes ("Ignacio Espinoza / Phorge Lab"
     → "Ignacio Espinoza") and trim whitespace.
  3. Merge — when two entries resolve to the same canonical name (exact match
     after normalisation, or one entry is a bare first-name version of another),
     keep the richer record and fold any unique non-empty fields from the other
     into it.
"""

from __future__ import annotations
from typing import Any


# ── Name helpers ─────────────────────────────────────────────────────────────

_UNKNOWN_NAMES = {"", "unknown", "unknown pi", "n/a", "none"}


def _canonical(name: str) -> str:
    """Strip lab-name suffix and normalise whitespace."""
    return name.split("/")[0].strip()


def _key(name: str) -> str:
    """Lower-cased canonical name used for comparisons."""
    return _canonical(name).lower()


def _is_unknown(name: str) -> bool:
    return _key(name) in _UNKNOWN_NAMES


def _same_pi(a: str, b: str) -> bool:
    """
    Return True if two name strings refer to the same person.

    Exact match after normalisation is the primary check.
    Bare-first-name match ("Simone" vs "Simone Yan") is the secondary check:
    accepted only when one side has a single token and the first tokens agree.
    """
    ka, kb = _key(a), _key(b)
    if ka == kb:
        return True
    ta, tb = ka.split(), kb.split()
    if not ta or not tb:
        return False
    # One side is a bare first name and the other starts with the same token
    if ta[0] == tb[0] and (len(ta) == 1 or len(tb) == 1):
        return True
    return False


# ── Richness scoring ──────────────────────────────────────────────────────────

def _richness(entry: dict[str, Any]) -> int:
    """Higher score = more complete entry; used to pick the primary record."""
    score = 0
    score += len(entry.get("research_areas") or []) * 3
    score += len(entry.get("recent_abstracts") or []) * 2
    score += len(entry.get("papers") or []) * 2
    score += bool(entry.get("pi_survey")) * 5
    score += len(entry.get("student_survey_responses") or []) * 4
    inst = entry.get("institution", "")
    score += bool(inst and inst.lower() not in ("unknown", "")) * 4
    dept = entry.get("department", "")
    score += bool(dept and "TODO" not in dept and dept.lower() != "unknown") * 2
    return score


# ── Merge logic ───────────────────────────────────────────────────────────────

def _merge(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """
    Merge secondary into primary.

    Primary wins on every field it already has a useful value for.
    Secondary fills in only fields that are absent or empty in primary.
    The canonical name of the longer/fuller string is kept.
    """
    merged = {**secondary, **{}}   # start from secondary as base
    for k, v in primary.items():
        prim_useful = (
            v is not None
            and v != []
            and v != {}
            and (not isinstance(v, str) or (v.strip() and "TODO" not in v and v.lower() != "unknown"))
        )
        if prim_useful:
            merged[k] = v
        elif k not in merged or not merged[k]:
            merged[k] = v

    # Keep whichever canonical name is more complete (longer)
    name_a = _canonical(primary.get("name", ""))
    name_b = _canonical(secondary.get("name", ""))
    merged["name"] = name_a if len(name_a) >= len(name_b) else name_b
    return merged


# ── Public entry point ────────────────────────────────────────────────────────

def dedup_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Given a flat list of raw seed dicts (possibly from multiple files):

      1. Drop entries with unknown/blank names.
      2. Normalise each name (strip lab suffix, trim whitespace).
      3. Merge any two entries that refer to the same PI, keeping the richer
         record and folding unique fields from the weaker one into it.

    Returns a deduplicated, normalised list ready for database insertion.
    """
    result: list[dict[str, Any]] = []

    for raw in entries:
        name = raw.get("name", "")

        if _is_unknown(name):
            print(f"[dedup] Dropped unknown entry: {repr(name)}")
            continue

        entry = {**raw, "name": _canonical(name)}

        # Try to find an existing result entry this should merge into
        merged = False
        for i, existing in enumerate(result):
            if _same_pi(entry["name"], existing["name"]):
                if _richness(entry) > _richness(existing):
                    result[i] = _merge(entry, existing)
                else:
                    result[i] = _merge(existing, entry)
                print(f"[dedup] Merged {repr(entry['name'])} → {repr(result[i]['name'])}")
                merged = True
                break

        if not merged:
            result.append(entry)

    return result
