#!/usr/bin/env python3
"""
import_survey_csv.py

Reads the Google Forms CSV export and produces a JSON seed file
(data/seeds/surveyed_pis.json) for PIs who filled out the PiMatch survey.

Usage:
    python3 data/import_survey_csv.py

Writes:  data/seeds/surveyed_pis.json

The output is compatible with POST /api/pi/seed and the auto-seed logic
in backend/main.py. Fields that require Semantic Scholar / NSF lookup
(research_areas, recent_abstracts, papers, nsf_grants, co_author_names)
are left as empty placeholders — fill them in before seeding.
"""

import csv
import json
import os
import sys

CSV_PATH = os.path.join(
    os.path.expanduser("~"),
    "Documents", "Mudd", "2026 Hacktech",
    "PiMatch Lab Fit Profile Survey (Responses) - Form Responses 1.csv",
)

OUT_PATH = os.path.join(os.path.dirname(__file__), "seeds", "surveyed_pis.json")

# ── Survey identifier → canonical full name + institution + department ────────
# Fill these in once you know each professor's affiliation.
PROFESSOR_META = {
    "Simone": {
        "name": "Simone Yan",
        "institution": "TODO: fill in institution",
        "department": "TODO: fill in department",
        "email": None,
        "lab_website": None,
        "location": "TODO: e.g. CA",
        "tier": 2,
        "lab_size": 5,
    },
    "Heidi": {
        "name": "Heidi Wu",
        "institution": "TODO: fill in institution",
        "department": "TODO: fill in department",
        "email": None,
        "lab_website": None,
        "location": "TODO: e.g. CA",
        "tier": 2,
        "lab_size": 5,
    },
}

# ── Text → numeric mappings for scoring.py ────────────────────────────────────
_MEETING_FREQ = {
    "daily":                      1,
    "multiple times per week":    1,
    "weekly":                     2,
    "biweekly":                   3,
    "monthly":                    4,
    "monthly or less":            5,
}

_MENTORSHIP_AUTONOMY = {
    "highly guided":              1,
    "moderately guided":          3,
    "collaborative":              3,
    "mostly independent":         4,
    "fully independent":          5,
}

_WORK_LIFE = {
    "strongly discouraged":       1,
    "discouraged":                2,
    "neutral":                    3,
    "encouraged":                 4,
    "strongly encouraged":        5,
}

_INTERVENTION = {
    "very high involvement":      1,
    "high involvement":           2,
    "moderate":                   3,
    "low involvement":            4,
    "minimal":                    5,
}


def _norm(s: str) -> str:
    return s.strip().lower()


def _meeting_num(text: str) -> int:
    for key, val in _MEETING_FREQ.items():
        if key in _norm(text):
            return val
    return 3  # default: biweekly


def _autonomy_num(text: str) -> int:
    for key, val in _MENTORSHIP_AUTONOMY.items():
        if key in _norm(text):
            return val
    return 3


def _wlb_num(text: str) -> int:
    for key, val in _WORK_LIFE.items():
        if key in _norm(text):
            return val
    return 3


def _intervention_num(text: str, autonomy: int) -> int:
    # Infer from autonomy: high autonomy → low intervention
    return max(1, min(5, 6 - autonomy))


def row_to_pi_survey(row: dict) -> dict:
    mentorship_text = row.get("How would you describe your mentorship style?", "")
    meeting_text    = row.get("How often do you meet with your PhD students 1:1?", "")
    wlb_text        = row.get("Work-life balance expectation ", "").strip() or \
                      row.get("Work-life balance expectation", "").strip()

    autonomy = _autonomy_num(mentorship_text)
    meeting_num = _meeting_num(meeting_text)
    intervention = _intervention_num("", autonomy)
    wlb = _wlb_num(wlb_text)

    return {
        # Narrative fields (used directly in the avatar system prompt)
        "research_priorities": "TODO: add research focus — see Semantic Scholar lookup",
        "mentorship_style": mentorship_text,
        "meeting_frequency": meeting_text,
        "lab_expectations": row.get("What are your expectations for PhD outcomes in your lab? ", "").strip()
                            or row.get("What are your expectations for PhD outcomes in your lab?", "").strip(),
        "student_qualities": row.get(
            "Which characteristics are most important for success in your lab? (Select up to 3)", ""
        ).strip(),
        "student_intake": row.get(
            "How many new PhD students do you typically take per year?", ""
        ).strip(),
        "student_support": row.get(
            "When a student is struggling, what is your typical response? ", ""
        ).strip(),
        "work_pattern": row.get("Typical working pattern in your lab", "").strip(),
        "project_assignment": row.get("How are projects typically assigned? ", "").strip()
                              or row.get("How are projects typically assigned?", "").strip(),
        "communication_style": row.get("Preferred communication style", "").strip(),
        "response_time": row.get("Expected email/Slack response time ", "").strip()
                        or row.get("Expected email/Slack response time", "").strip(),
        "lab_environment": row.get("Lab environment", "").strip(),
        "work_life_balance_text": wlb_text,
        "funding_stability_text": row.get(
            "How stable is funding for incoming PhD students? ", ""
        ).strip() or row.get("How stable is funding for incoming PhD students?", "").strip(),
        "funding_source": row.get("Typical funding source ", "").strip()
                         or row.get("Typical funding source", "").strip(),
        "phd_outcomes": row.get(
            "What are your expectations for PhD outcomes in your lab? ", ""
        ).strip(),
        "graduation_timeline": row.get("Typical time to graduation: ", "").strip()
                               or row.get("Typical time to graduation:", "").strip(),
        "success_traits": row.get(
            "In 1–2 sentences, what distinguishes your most successful students? ", ""
        ).strip() or row.get(
            "In 1–2 sentences, what distinguishes your most successful students?", ""
        ).strip(),
        "poor_fit_traits": row.get(
            "Which traits tend to be poor fits for your lab? (Select up to 3) ", ""
        ).strip(),
        "critical_mismatch": row.get(
            "Which mismatch is most problematic in your lab? ", ""
        ).strip(),
        "struggle_reason": row.get(
            "In 1–2 sentences, what is a common reason students struggle or leave your lab?", ""
        ).strip(),
        "daily_experience": row.get(
            "How would you describe the day-to-day experience in your lab? ", ""
        ).strip(),
        "working_style": row.get(
            "What best describes your lab's working style? ", ""
        ).strip(),
        "lab_tone": row.get(
            "How would you describe the overall tone of your lab? ", ""
        ).strip(),
        "lab_description": row.get(
            'If a prospective student asks: "What is it like to work in your lab?", how would you respond? (2–3 sentences)',
            ""
        ).strip(),
        "interview_questions": row.get(
            "What questions do you commonly ask during PhD interviews? (Select up to 3) ", ""
        ).strip(),
        "additional_notes": row.get(
            "Is there anything important about your lab, mentorship style, or expectations that was not captured above but you would like prospective students to know?",
            ""
        ).strip(),
        "key_fit_factors": row.get(
            "Which aspects of this survey do you consider most important for determining student–lab fit?",
            ""
        ).strip(),

        # Numeric fields consumed by scoring.py
        "autonomy_style":        autonomy,
        "meeting_frequency_num": meeting_num,
        "intervention_level":    intervention,
        "work_life_balance":     wlb,
    }


def row_to_pi_profile(identifier: str, row: dict) -> dict:
    meta = PROFESSOR_META[identifier]
    pi_survey = row_to_pi_survey(row)

    # Derive is_recruiting from student intake
    intake = row.get("How many new PhD students do you typically take per year?", "").strip()
    is_recruiting = intake not in ("0", "0–1", "")

    # Derive has_active_nsf_grant from funding source
    funding_src = row.get("Typical funding source ", "").strip().lower()
    has_nsf = "grant" in funding_src or "nsf" in funding_src

    return {
        **meta,
        # Research fields — FILL IN after Semantic Scholar lookup
        "semantic_scholar_id": None,
        "research_areas": [],           # TODO: add from Semantic Scholar / lab website
        "recent_abstracts": [],         # TODO: add 3–5 recent abstracts
        "co_author_ids": [],
        "co_author_names": [],
        "papers_last_12_months": 0,     # TODO: update after lookup
        "papers": [],                   # TODO: add [{title, url, venue, year}, ...]
        # Funding — FILL IN after NSF lookup
        "nsf_grants": [],               # TODO: add from NSF Reporter
        "has_active_nsf_grant": has_nsf,
        "total_active_funding_usd": None,
        "funding_citizen_restricted": False,
        # Classification
        "is_recruiting": is_recruiting,
        # Survey data
        "pi_survey": pi_survey,
        "student_survey_responses": [],  # no student responses in this CSV
        "reply_likelihood": None,
    }


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at:\n  {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    profiles = []
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            identifier = row.get("Lab Name", "").strip()
            if identifier in PROFESSOR_META:
                profile = row_to_pi_profile(identifier, row)
                profiles.append(profile)
                print(f"  Imported: {profile['name']}")
            else:
                ts = row.get("Timestamp", "?")
                print(f"  Skipped row (timestamp={ts}, lab_name={repr(identifier)})")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(profiles)} profile(s) to {OUT_PATH}")
    print("\nNext steps:")
    print("  1. Fill in institution/department in PROFESSOR_META at the top of this script")
    print("  2. Run Session 1 to add research_areas, recent_abstracts, papers, nsf_grants")
    print("  3. POST /api/pi/seed with file_path pointing to surveyed_pis.json")


if __name__ == "__main__":
    main()
