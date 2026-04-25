"""
survey_loader.py

Parses Google Form CSV exports from the two PiMatch surveys and converts
them into structured dicts ready to seed as PIProfile entries.

Usage (run from project root):
    python3 data/survey_loader.py

Outputs:
    data/seeds/keck_pis.json   ← one entry per PI respondent, with
                                  pi_survey and student_survey_responses populated
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Field mappings  (CSV header → internal normalized key)
# Strip trailing spaces +   (LINE SEPARATOR from Google Forms) at load time.
# ---------------------------------------------------------------------------

PI_FIELD_MAP: Dict[str, str] = {
    "How many new PhD students do you typically take per year?":             "intake_per_year",
    "How would you describe your mentorship style?":                         "mentorship_style",
    "How often do you meet with your PhD students 1:1?":                     "meeting_frequency",
    "When a student is struggling, what is your typical response?":          "struggle_response",
    "Typical working pattern in your lab":                                   "working_pattern",
    "How are projects typically assigned?":                                  "project_assignment",
    "Preferred communication style":                                         "communication_style",
    "Expected email/Slack response time":                                    "response_time",
    "Lab environment":                                                       "lab_environment",
    "Work-life balance expectation":                                         "work_life_balance",
    "How stable is funding for incoming PhD students?":                      "funding_stability",
    "Typical funding source":                                                "funding_source",
    "What are your expectations for PhD outcomes in your lab?":              "outcome_expectations",
    "Typical time to graduation:":                                           "time_to_graduation",
    "Students are expected to pursue:":                                      "industry_academia_preference",
    "Which characteristics are most important for success in your lab? (Select up to 3)": "student_qualities",
    "In 1–2 sentences, what distinguishes your most successful students?":            "successful_student_description",
    "Which traits tend to be poor fits for your lab? (Select up to 3)":     "poor_fit_traits",
    "Which mismatch is most problematic in your lab?":                       "common_mismatch",
    "In 1–2 sentences, what is a common reason students struggle or leave your lab?": "struggle_reason",
    "How would you describe the day-to-day experience in your lab?":        "daily_experience",
    "What best describes your lab’s working style?":                    "working_style",
    "How would you describe the overall tone of your lab?":                  "lab_tone",
    'If a prospective student asks: “What is it like to work in your lab?”, how would you respond? (2–3 sentences)': "lab_description_pitch",
    "What questions do you commonly ask during PhD interviews? (Select up to 3)": "interview_questions",
    "Is there anything important about your lab, mentorship style, or expectations that was not captured above but you would like prospective students to know?": "additional_notes",
    "Which aspects of this survey do you consider most important for determining student–lab fit?": "fit_priorities",
}

STUDENT_FIELD_MAP: Dict[str, str] = {
    "What is your current role?":                                            "role",
    "How long have you been in the lab?":                                    "tenure",
    "How would you describe your PI’s mentorship style in practice?":   "mentorship_reality",
    "How often do you actually meet your PI 1:1?":                           "meeting_frequency_reality",
    "When you struggle, what typically happens?":                            "struggle_reality",
    "How would you describe your PI’s communication style?":            "communication_style_reality",
    "How demanding is your PI in practice?":                                 "demanding_level",
    "How comfortable do you feel giving feedback or asking questions":        "feedback_comfort",
    "What is the actual working pattern in your lab?":                       "working_pattern_reality",
    "How would you describe the lab culture in practice?":                   "lab_culture",
    "Work-life balance in reality":                                          "work_life_balance_reality",
    "How aligned are expectations between you and your PI?":                 "expectation_alignment",
    "What type of student tends to succeed in your lab?":                    "success_profile",
    "What type of student tends to struggle?":                               "struggle_profile",
    "What is the most common source of mismatch?":                           "mismatch_source",
    "Compared to how your PI might describe the lab, how different is the reality?": "pi_vs_reality",
    "If different, what is the main difference?":                            "pi_vs_reality_detail",
    "What is one thing you wish you knew before joining this lab?":          "wish_knew",
    "How would you describe what it is actually like to work in this lab?":  "overall_experience",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_key(raw: str) -> str:
    """Normalize a CSV header: strip whitespace/line-separators, fold smart quotes to ASCII."""
    # Strip leading/trailing whitespace including Unicode line/paragraph separators
    s = raw.strip().strip("\u2028\u2029").strip()
    # Fold smart/curly quotes to straight ASCII equivalents
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    return s


# Pre-build a normalized lookup table so CSV keys and map keys are compared
# after the same normalization pass (handles smart quotes in either source).
_PI_FIELD_MAP_NORMALIZED: Dict[str, str] = {}
_STUDENT_FIELD_MAP_NORMALIZED: Dict[str, str] = {}


def _build_normalized_maps() -> None:
    global _PI_FIELD_MAP_NORMALIZED, _STUDENT_FIELD_MAP_NORMALIZED
    _PI_FIELD_MAP_NORMALIZED      = {_clean_key(k): v for k, v in PI_FIELD_MAP.items()}
    _STUDENT_FIELD_MAP_NORMALIZED = {_clean_key(k): v for k, v in STUDENT_FIELD_MAP.items()}


def _normalize_row(raw_row: Dict[str, str], field_map_normalized: Dict[str, str]) -> Dict[str, str]:
    """Apply a pre-normalized field_map to a raw CSV row, skipping empty values."""
    out: Dict[str, str] = {}
    for raw_key, value in raw_row.items():
        cleaned = _clean_key(raw_key)
        internal_key = field_map_normalized.get(cleaned)
        if internal_key and value.strip():
            out[internal_key] = value.strip()
    return out


# Build normalized maps at import time so they're ready when load_* is called
_build_normalized_maps()


def _canonical_lab_name(raw: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for fuzzy matching."""
    s = raw.lower().strip()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_pi_surveys(csv_path: str) -> List[Dict[str, Any]]:
    """
    Parse the PI survey CSV.
    Returns a list of dicts with normalized keys plus raw identity fields.
    """
    results = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            consent = row.get("Consent", "").strip()
            if "agree to participate" not in consent.lower():
                continue

            survey = _normalize_row(row, _PI_FIELD_MAP_NORMALIZED)

            lab_name   = row.get("Lab Name", "").strip()
            institution = row.get("Institution / University", "").strip()
            department  = row.get("Department / Program", "").strip()
            demo_ok     = "prefer" not in row.get("Demo Permission", "").lower()

            results.append({
                "lab_name":    lab_name,
                "institution": institution,
                "department":  department,
                "demo_ok":     demo_ok,
                "pi_survey":   survey,
            })
    return results


def load_student_surveys(csv_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse the student survey CSV.
    Returns {canonical_lab_name: [normalized_response, ...]}.
    """
    by_lab: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            consent = row.get("Information Usage", "").strip()
            if "agree to participate" not in consent.lower():
                continue

            demo_ok = "prefer" not in row.get("Demo Permission", "").lower()
            lab_raw = row.get("Lab Name (if applicable)", "").strip()
            lab_key = _canonical_lab_name(lab_raw)

            response = _normalize_row(row, _STUDENT_FIELD_MAP_NORMALIZED)
            response["_demo_ok"] = str(demo_ok)
            by_lab[lab_key].append(response)

    return dict(by_lab)


def match_students_to_pis(
    pi_entries: List[Dict[str, Any]],
    student_by_lab: Dict[str, List[Dict[str, str]]],
) -> List[Dict[str, Any]]:
    """
    Join student responses to PI entries by fuzzy lab-name matching.
    Aggregates across all matching student-lab keys (handles typos / duplicate
    entries where one lab appears under two slightly different canonical names).
    Returns the same pi_entries list with student_survey_responses populated.
    """
    stopwords = {"lab", "the", "a", "of", "and"}

    for entry in pi_entries:
        lab_key = _canonical_lab_name(entry["lab_name"])
        pi_words = set(lab_key.split()) - stopwords
        matched: List[Dict[str, str]] = []

        for s_key, responses in student_by_lab.items():
            # Direct match
            if s_key == lab_key:
                matched.extend(responses)
                continue
            s_words = set(s_key.split()) - stopwords
            meaningful = pi_words & s_words
            # Require 2 common words when PI has multiple words; 1 suffices for
            # single-identifier lab names.
            threshold = 2 if len(pi_words) >= 3 else 1
            if len(meaningful) >= threshold:
                matched.extend(responses)
                continue
            # Fallback: match on any long token (>5 chars) that appears in both
            # sides, handling single-character typos (e.g. "lgnacio" ≈ "ignacio").
            long_pi = {w for w in pi_words if len(w) > 5}
            long_s  = {w for w in s_words  if len(w) > 5}
            if any(
                abs(len(pw) - len(sw)) <= 1 and
                sum(a != b for a, b in zip(pw, sw)) <= 1
                for pw in long_pi for sw in long_s
            ):
                matched.extend(responses)

        # Strip internal meta keys before storing
        entry["student_survey_responses"] = [
            {k: v for k, v in r.items() if not k.startswith("_")}
            for r in matched
        ]

    return pi_entries


def build_seed_entries(pi_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert joined PI + student entries into PIProfile seed dicts.
    Research fields (abstracts, papers, grants) are left as stubs —
    fill them in manually or via the Semantic Scholar loader.
    """
    seeds = []
    for entry in pi_entries:
        survey = entry["pi_survey"]

        # Infer research_areas from survey text where available
        research_areas: List[str] = []
        pitch = survey.get("lab_description_pitch", "")
        if "intersection of" in pitch.lower():
            # e.g. "intersection of molecular biology, data science, microbiology and synbio"
            after = pitch.lower().split("intersection of")[-1]
            parts = re.split(r"[,\n]| and ", after)
            research_areas = [p.strip().rstrip(".") for p in parts if len(p.strip()) > 2][:5]

        seed: Dict[str, Any] = {
            "name":        entry["lab_name"] or "Unknown PI",
            "institution": entry["institution"] or "Unknown",
            "department":  entry["department"] or "Unknown",
            "email":       None,
            "lab_website": None,

            # Research (stubs — fill with Semantic Scholar data)
            "semantic_scholar_id": None,
            "research_areas":      research_areas,
            "recent_abstracts":    [],
            "co_author_ids":       [],
            "co_author_names":     [],
            "papers_last_12_months": 0,
            "papers":              [],

            # Funding (stubs)
            "nsf_grants":               [],
            "has_active_nsf_grant":     False,
            "total_active_funding_usd": None,
            "funding_citizen_restricted": False,

            # Classification
            "tier":         3,
            "location":     "",
            "lab_size":     5,
            "is_recruiting": True,
            "reply_likelihood": "medium",

            # Survey data (the rich part)
            "pi_survey":               survey,
            "student_survey_responses": entry["student_survey_responses"],
        }
        seeds.append(seed)

    return seeds


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))

    pi_csv = os.path.join(
        os.path.expanduser("~"),
        "Documents", "Mudd", "2026 Hacktech",
        "PiMatch Lab Fit Profile Survey (Responses) - Form Responses 1.csv",
    )
    student_csv = os.path.join(
        os.path.expanduser("~"),
        "Documents", "Mudd", "2026 Hacktech",
        "Helping Prospective Students Understand Your Lab (Responses) - Form Responses 1.csv",
    )

    if not os.path.exists(pi_csv):
        sys.exit(f"PI CSV not found: {pi_csv}")
    if not os.path.exists(student_csv):
        sys.exit(f"Student CSV not found: {student_csv}")

    pi_entries = load_pi_surveys(pi_csv)
    student_by_lab = load_student_surveys(student_csv)
    joined = match_students_to_pis(pi_entries, student_by_lab)
    seeds = build_seed_entries(joined)

    out_path = os.path.join(base, "seeds", "keck_pis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, indent=2, ensure_ascii=False)

    print(f"Written {len(seeds)} PI entries to {out_path}")
    for s in seeds:
        n_students = len(s["student_survey_responses"])
        print(f"  {s['name']} @ {s['institution']} — {len(s['pi_survey'])} PI fields, {n_students} student response(s)")
