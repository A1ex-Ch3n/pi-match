#!/usr/bin/env python3
"""
import_survey_csv.py

Reads the PI survey CSV and the student feedback CSV and produces
data/seeds/surveyed_pis.json — ready for POST /api/pi/seed.

Usage:
    python3 data/import_survey_csv.py

Fields that require a Semantic Scholar / NSF lookup are left as empty
placeholders — fill them in before seeding.
"""

import csv
import json
import os
import sys

PI_CSV_PATH = os.path.join(
    os.path.expanduser("~"),
    "Documents", "Mudd", "2026 Hacktech",
    "PiMatch Lab Fit Profile Survey (Responses) - Form Responses 1.csv",
)

STUDENT_CSV_PATH = os.path.join(
    os.path.expanduser("~"),
    "Documents", "Mudd", "2026 Hacktech",
    "Helping Prospective Students Understand Your Lab (Responses) - Form Responses 1.csv",
)

OUT_PATH = os.path.join(os.path.dirname(__file__), "seeds", "surveyed_pis.json")


# ── Professor identity & known metadata ──────────────────────────────────────
# "Lab Name" field value from the PI survey CSV → profile metadata
PROFESSOR_META = {
    "Simone": {
        "name": "Simone Yan",
        "institution": "National Taiwan University",
        "department": "TODO: fill in department",
        "email": None,
        "lab_website": None,
        "location": "TW",
        "tier": 2,
        "lab_size": 5,
        "demo_internal_only": False,
    },
    "Heidi": {
        "name": "Heidi Wu",
        "institution": "National Taiwan University",
        "department": "TODO: fill in department",
        "email": None,
        "lab_website": None,
        "location": "TW",
        "tier": 2,
        "lab_size": 5,
        "demo_internal_only": False,
    },
    "Ignacio Espinoza / Phorge Lab": {
        "name": "Ignacio Espinoza",
        "institution": "Keck Graduate Institute",
        "department": "School of Life Sciences",
        "lab_name": "Phorge Lab",
        "email": None,
        "lab_website": None,
        "location": "CA",
        "tier": 2,
        "lab_size": 3,
        "demo_internal_only": True,   # PI requested internal use only
    },
}

# ── Student response → professor key lookup ──────────────────────────────────
# Normalised substrings that identify which professor a student response belongs to
_STUDENT_LAB_PATTERNS = {
    "phorge":    "Ignacio Espinoza / Phorge Lab",
    "espinoza":  "Ignacio Espinoza / Phorge Lab",
    # Add e.g. "simone": "Simone", "heidi wu": "Heidi" when student forms exist
}


def _match_student_to_pi(lab_name_raw: str) -> str | None:
    normalised = lab_name_raw.lower()
    for pattern, pi_key in _STUDENT_LAB_PATTERNS.items():
        if pattern in normalised:
            return pi_key
    return None


# ── Text → numeric helpers ───────────────────────────────────────────────────

def _meeting_num(text: str) -> int:
    t = text.strip().lower()
    if "daily"              in t: return 1
    if "multiple"           in t: return 1
    if "weekly"             in t: return 2
    if "biweekly"           in t: return 3
    if "monthly"            in t: return 4
    return 3

def _autonomy_num(text: str) -> int:
    t = text.strip().lower()
    if "highly guided"      in t: return 1
    if "very hands-on"      in t: return 2
    if "moderately guided"  in t: return 3
    if "mostly independent" in t: return 4
    if "fully independent"  in t: return 5
    return 3

def _wlb_num(text: str) -> int:
    t = text.strip().lower()
    if "strongly discouraged" in t: return 1
    if "discouraged"          in t: return 2
    if "neutral"              in t: return 3
    if "encouraged"           in t: return 4
    if "strongly encouraged"  in t: return 5
    return 3

def _norm_key(k: str) -> str:
    """Strip whitespace and Unicode line-separator chars (Google Forms artifact)."""
    return k.replace("\u2028", "").replace("\u2029", "").replace("\u2019", "'").strip()


def _normalize_row(row: dict) -> dict:
    return {_norm_key(k): v.strip() for k, v in row.items()}


def _strip(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(_norm_key(k), "").strip()
        if v:
            return v
    return ""


# ── PI survey row → pi_survey dict ───────────────────────────────────────────

def row_to_pi_survey(row: dict) -> dict:
    mentorship_text = _strip(row, "How would you describe your mentorship style?")
    meeting_text    = _strip(row, "How often do you meet with your PhD students 1:1?")
    wlb_text        = _strip(row, "Work-life balance expectation ", "Work-life balance expectation")

    autonomy     = _autonomy_num(mentorship_text)
    meeting_num  = _meeting_num(meeting_text)
    wlb          = _wlb_num(wlb_text)
    intervention = max(1, min(5, 6 - autonomy))   # high autonomy → low intervention

    return {
        # Core fields validated by profile_builder.py
        "research_priorities": "TODO: add research focus — fill from Semantic Scholar / lab website",
        "mentorship_style":    mentorship_text,
        "meeting_frequency":   meeting_text,
        "lab_expectations":    _strip(row,
            "What are your expectations for PhD outcomes in your lab? ",
            "What are your expectations for PhD outcomes in your lab?"),
        "student_qualities":   _strip(row,
            "Which characteristics are most important for success in your lab? (Select up to 3)"),
        # Numeric fields for scoring.py
        "autonomy_style":        autonomy,
        "meeting_frequency_num": meeting_num,
        "intervention_level":    intervention,
        "work_life_balance":     wlb,
        # Extended narrative fields for richer avatar voice
        "student_intake":    _strip(row, "How many new PhD students do you typically take per year?"),
        "student_support":   _strip(row, "When a student is struggling, what is your typical response? ",
                                        "When a student is struggling, what is your typical response?"),
        "work_pattern":      _strip(row, "Typical working pattern in your lab"),
        "project_assignment": _strip(row, "How are projects typically assigned? ",
                                         "How are projects typically assigned?"),
        "communication_style": _strip(row, "Preferred communication style"),
        "response_time":     _strip(row, "Expected email/Slack response time ",
                                        "Expected email/Slack response time"),
        "lab_environment":   _strip(row, "Lab environment"),
        "funding_stability_text": _strip(row,
            "How stable is funding for incoming PhD students? ",
            "How stable is funding for incoming PhD students?"),
        "funding_source":    _strip(row, "Typical funding source ", "Typical funding source"),
        "graduation_timeline": _strip(row, "Typical time to graduation: ", "Typical time to graduation:"),
        "success_traits":    _strip(row,
            "In 1–2 sentences, what distinguishes your most successful students? ",
            "In 1–2 sentences, what distinguishes your most successful students?"),
        "poor_fit_traits":   _strip(row,
            "Which traits tend to be poor fits for your lab? (Select up to 3) "),
        "critical_mismatch": _strip(row, "Which mismatch is most problematic in your lab? "),
        "struggle_reason":   _strip(row,
            "In 1–2 sentences, what is a common reason students struggle or leave your lab?"),
        "daily_experience":  _strip(row, "How would you describe the day-to-day experience in your lab? "),
        "working_style":     _strip(row, "What best describes your lab's working style? "),
        "lab_tone":          _strip(row, "How would you describe the overall tone of your lab? "),
        "lab_description":   _strip(row,
            'If a prospective student asks: "What is it like to work in your lab?", how would you respond? (2–3 sentences)'),
        "interview_questions": _strip(row,
            "What questions do you commonly ask during PhD interviews? (Select up to 3) "),
        "additional_notes":  _strip(row,
            "Is there anything important about your lab, mentorship style, or expectations that was not captured above but you would like prospective students to know?"),
        "key_fit_factors":   _strip(row,
            "Which aspects of this survey do you consider most important for determining student–lab fit?"),
    }


# ── Student feedback row → student_survey_response dict ──────────────────────

def _derive_publication_rate(demands_text: str, pi_outcomes: str = "") -> str:
    t = demands_text.lower()
    if "very high" in t or "intense" in t:
        return "High — PI maintains an intense pace with strong publication expectations"
    if "high" in t:
        return "Moderately high — publications are expected but timeline is flexible"
    return "Moderate — publications expected; exact pace depends on the project"


def student_row_to_response(row: dict) -> dict:
    demands_text = _strip(row, "How demanding is your PI in practice? ",
                               "How demanding is your PI in practice?")
    return {
        # Required keys (profile_builder.py validates these exist)
        "overall_experience": _strip(row,
            "How would you describe what it is actually like to work in this lab? ",
            "How would you describe what it is actually like to work in this lab?"),
        "mentorship": (
            _strip(row, "How would you describe your PI's mentorship style in practice? ",
                        "How would you describe your PI's mentorship style in practice?")
            + " — meets "
            + _strip(row, "How often do you actually meet your PI 1:1? ",
                         "How often do you actually meet your PI 1:1?")
        ).strip(" —"),
        "work_life_balance": _strip(row, "Work-life balance in reality ",
                                        "Work-life balance in reality"),
        "publication_rate":  _derive_publication_rate(demands_text),
        "lab_culture":       _strip(row,
            "How would you describe the lab culture in practice? ",
            "How would you describe the lab culture in practice?"),
        # Extended fields for richer avatar voice
        "when_struggling":       _strip(row, "When you struggle, what typically happens? ",
                                            "When you struggle, what typically happens?"),
        "communication":         _strip(row, "How would you describe your PI's communication style? ",
                                            "How would you describe your PI's communication style?"),
        "demands":               demands_text,
        "comfort_with_feedback": _strip(row,
            "How comfortable do you feel giving feedback or asking questions",
            "How comfortable do you feel giving feedback or asking questions "),
        "work_pattern":          _strip(row, "What is the actual working pattern in your lab? ",
                                            "What is the actual working pattern in your lab?"),
        "expectations_alignment": _strip(row, "How aligned are expectations between you and your PI?",
                                             "How aligned are expectations between you and your PI? "),
        "success_type":          _strip(row, "What type of student tends to succeed in your lab?",
                                            "What type of student tends to succeed in your lab? "),
        "struggle_type":         _strip(row, "What type of student tends to struggle? ",
                                            "What type of student tends to struggle?"),
        "common_mismatch":       _strip(row, "What is the most common source of mismatch?",
                                            "What is the most common source of mismatch? "),
        "reality_vs_pi":         _strip(row,
            "Compared to how your PI might describe the lab, how different is the reality?",
            "Compared to how your PI might describe the lab, how different is the reality? "),
        "main_difference":       _strip(row, " If different, what is the main difference? ",
                                            "If different, what is the main difference?"),
        "wish_knew":             _strip(row,
            "What is one thing you wish you knew before joining this lab? ",
            "What is one thing you wish you knew before joining this lab?"),
        "tenure":                _strip(row, "How long have you been in the lab? ",
                                            "How long have you been in the lab?"),
    }


# ── Build full PIProfile seed entry ──────────────────────────────────────────

def build_pi_profile(pi_key: str, pi_row: dict, student_rows: list[dict]) -> dict:
    meta = PROFESSOR_META[pi_key]
    pi_survey = row_to_pi_survey(pi_row)

    intake = _strip(pi_row, "How many new PhD students do you typically take per year?")
    is_recruiting = intake not in ("0", "0–1", "")

    funding_src = _strip(pi_row, "Typical funding source ", "Typical funding source").lower()
    has_nsf = "nsf" in funding_src  # KGI uses non-NSF grants; NTU uses MOST

    student_responses = [student_row_to_response(r) for r in student_rows]

    # Strip internal-only fields from public-facing meta
    public_meta = {k: v for k, v in meta.items()
                   if k not in ("demo_internal_only", "lab_name")}

    return {
        **public_meta,
        "semantic_scholar_id": None,
        "research_areas":      [],       # TODO: fill from Semantic Scholar / lab website
        "recent_abstracts":    [],       # TODO: fill from Semantic Scholar
        "co_author_ids":       [],
        "co_author_names":     [],
        "papers_last_12_months": 0,      # TODO: update after lookup
        "papers":              [],       # TODO: [{title, url, venue, year}]
        "nsf_grants":          [],       # TODO: fill (NSF for US; MOST for TW)
        "has_active_nsf_grant":  has_nsf,
        "total_active_funding_usd": None,
        "funding_citizen_restricted": False,
        "is_recruiting": is_recruiting,
        "pi_survey": pi_survey,
        "student_survey_responses": student_responses,
        "reply_likelihood": None,
        # Retain internal flag separately so downstream scripts can filter demo vs internal
        "_demo_internal_only": meta.get("demo_internal_only", False),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    for path, label in [(PI_CSV_PATH, "PI survey"), (STUDENT_CSV_PATH, "Student survey")]:
        if not os.path.exists(path):
            print(f"ERROR: {label} CSV not found:\n  {path}", file=sys.stderr)
            sys.exit(1)

    # Read PI survey rows
    pi_rows: dict[str, dict] = {}
    with open(PI_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = _normalize_row(raw)
            key = raw.get("Lab Name", "").strip()
            if key in PROFESSOR_META:
                pi_rows[key] = row
                print(f"  PI row found:      {PROFESSOR_META[key]['name']}")
            else:
                print(f"  PI row skipped:    lab_name={repr(key)}")

    # Read student survey rows, grouped by PI key
    student_rows: dict[str, list[dict]] = {k: [] for k in PROFESSOR_META}
    with open(STUDENT_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = _normalize_row(raw)
            lab_raw = raw.get("Lab Name (if applicable)", "").strip()
            pi_key  = _match_student_to_pi(lab_raw)
            if pi_key:
                student_rows[pi_key].append(row)
                name = PROFESSOR_META[pi_key]["name"]
                tenure = _strip(row, "How long have you been in the lab? ")
                print(f"  Student row found: {name} ({tenure})")
            else:
                print(f"  Student row skipped: lab_name={repr(lab_raw)}")

    # Build profiles
    profiles = []
    for pi_key, pi_row in pi_rows.items():
        profile = build_pi_profile(pi_key, pi_row, student_rows.get(pi_key, []))
        profiles.append(profile)
        n_students = len(profile["student_survey_responses"])
        internal   = profile.get("_demo_internal_only", False)
        print(f"  Built: {profile['name']} — {n_students} student response(s)"
              f"{' [INTERNAL ONLY]' if internal else ''}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(profiles)} profile(s) → {OUT_PATH}")
    print("\nRemaining TODOs per profile:")
    for p in profiles:
        todos = [f for f in ("department", "institution") if "TODO" in str(p.get(f, ""))]
        todos += ["research_areas"] if not p["research_areas"] else []
        todos += ["recent_abstracts"] if not p["recent_abstracts"] else []
        todos += ["papers"] if not p["papers"] else []
        if todos:
            print(f"  {p['name']}: {', '.join(todos)}")
        else:
            print(f"  {p['name']}: all fields complete ✓")


if __name__ == "__main__":
    main()
