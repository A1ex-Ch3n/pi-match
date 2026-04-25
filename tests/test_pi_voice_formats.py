#!/usr/bin/env python3
"""
tests/test_pi_voice_formats.py  —  Issue 2 verification

Verifies _format_pi_voice() handles BOTH survey key formats:
  - Seed format  (caltech_pis.json / import_survey_csv.py keys)
  - Real format  (keck_pis.json   / survey_loader.py keys)

Pass criteria: neither output is blank AND each renders >= 5 fields.
Does not modify any existing file.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agents.pi_avatar import _format_pi_voice

# ── Synthetic seed-format dict  (import_survey_csv.py row_to_pi_survey keys) ──
SEED_SURVEY = {
    "research_priorities":   "Developing ML methods for protein folding and single-cell genomics.",
    "mentorship_style":      "Weekly 1:1s with high autonomy between meetings.",
    "meeting_frequency":     "Weekly",
    "lab_expectations":      "Two first-author papers before graduation.",
    "student_qualities":     "Strong Python skills, curiosity, comfort with ambiguity.",
    "autonomy_style":        4,
    "intervention_level":    2,
    "work_life_balance":     4,
    "student_support":       "We reframe the problem together and set a 2-week recovery plan.",
    "work_pattern":          "Core hours 10am–4pm; fully flexible otherwise.",
    "project_assignment":    "Mix of PI-proposed and student-driven projects.",
    "response_time":         "Within 24 hours on weekdays.",
    "lab_environment":       "Collaborative open office.",
    "funding_stability_text":"NSF-funded through 2027; bridge funding available.",
    "funding_source":        "NSF CAREER + NIH R01",
    "graduation_timeline":   "4.5–5.5 years on average.",
    "success_traits":        "Intellectual honesty and willingness to pivot when data says so.",
    "poor_fit_traits":       "Students who need daily direction.",
    "critical_mismatch":     "Expecting a tight deliverables roadmap from day one.",
    "struggle_reason":       "Over-commitment to too many projects simultaneously.",
    "daily_experience":      "Independent deep work, weekly group meeting, ad-hoc Slack.",
    "working_style":         "Async-first; presence at group meetings required.",
    "lab_tone":              "Supportive but rigorous.",
    "lab_description":       "A small lab where every student owns a major research thread.",
    "additional_notes":      "Industry collaborations actively encouraged.",
}

# ── Synthetic real-format dict  (survey_loader.py PI_FIELD_MAP keys) ──────────
REAL_SURVEY = {
    "lab_description_pitch":       "We study viral ecology at the intersection of molecular biology and data science.",
    "mentorship_style":            "Mostly autonomous — I trust students to drive their own projects.",
    "meeting_frequency":           "Every two weeks 1:1; weekly group meeting.",
    "struggle_response":           "I check in more frequently and help re-scope the problem.",
    "working_pattern":             "Flexible hours, results-oriented, async-first.",
    "project_assignment":          "Students propose their own projects after a 3-month onboarding rotation.",
    "communication_style":         "Slack preferred; I respond within a business day.",
    "response_time":               "Same day urgent; 24 hours otherwise.",
    "lab_environment":             "Hybrid — some wet lab, significant computational work from home.",
    "work_life_balance":           "Encouraged — I expect students to take real vacations.",
    "funding_stability":           "Fully funded for 5 years through NIH R01.",
    "funding_source":              "NIH R01 + NSF CAREER",
    "outcome_expectations":        "At least 2 first-author publications and a public software tool.",
    "time_to_graduation":          "Median 5 years; range 4–6 years.",
    "student_qualities":           "Curiosity, rigor, and the ability to communicate results simply.",
    "successful_student_description": "Students who ask 'why' before 'how' and own their research narrative.",
    "poor_fit_traits":             "Students who need daily task lists.",
    "common_mismatch":             "Expecting frequent structured guidance in an autonomous environment.",
    "struggle_reason":             "Under-estimating how open-ended PhD research actually is.",
    "daily_experience":            "Morning: independent research. Afternoon: collaboration and meetings.",
    "working_style":               "Deep-focus blocks in the morning; collaborative afternoons.",
    "lab_tone":                    "Warm but intellectually demanding.",
    "additional_notes":            "~40% of graduates go to biotech; internships actively supported.",
}

SEP = "=" * 64

def run(label: str, survey: dict) -> bool:
    output = _format_pi_voice(survey)
    print(f"\n{SEP}")
    print(f"  {label}")
    print(SEP)
    if not output or not output.strip():
        print("  !! OUTPUT IS BLANK — FAIL")
        return False
    print(output)
    rendered = [l for l in output.splitlines() if l.strip().startswith("-")]
    print(f"\n  → {len(rendered)} field(s) rendered")
    return len(rendered) >= 5

seed_ok = run("SEED FORMAT  (import_survey_csv.py keys)", SEED_SURVEY)
real_ok = run("REAL FORMAT  (survey_loader.py keys)",    REAL_SURVEY)

# ── Key-coverage spot-checks ──────────────────────────────────────────────────
def check(label, output, marker):
    ok = marker.lower() in output.lower()
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok

seed_out = _format_pi_voice(SEED_SURVEY)
real_out = _format_pi_voice(REAL_SURVEY)

# work_pattern is shadowed by working_style when both are present (by design).
# Test it in isolation: a dict with ONLY work_pattern, no working_style.
work_pattern_only_out = _format_pi_voice({"work_pattern": "Core hours 10am–4pm; flexible otherwise."})

print(f"\n{SEP}")
print("  Spot-checks")
print(SEP)
checks = [
    # seed-only keys
    check("seed: lab_description → pitch",              seed_out,              "small lab where every student"),
    check("seed: success_traits → best students",       seed_out,              "intellectual honesty"),
    check("seed: student_support → struggling",         seed_out,              "when a student is struggling"),
    check("seed: work_pattern fallback (isolated)",     work_pattern_only_out, "10am"),
    check("seed: graduation_timeline → timeline",       seed_out,              "time to graduation"),
    check("seed: funding_stability_text → funding",     seed_out,              "NSF-funded"),
    check("seed: critical_mismatch → mismatch",         seed_out,              "tight deliverables"),
    check("seed: struggle_reason",                      seed_out,              "over-commitment"),
    check("seed: daily_experience",                     seed_out,              "deep work"),
    # real-only keys
    check("real: lab_description_pitch → pitch",    real_out, "viral ecology"),
    check("real: successful_student_description",   real_out, "ask 'why' before 'how'"),
    check("real: struggle_response → struggling",   real_out, "when a student is struggling"),
    check("real: working_pattern → working style",  real_out, "deep-focus"),
    check("real: time_to_graduation → timeline",    real_out, "time to graduation"),
    check("real: funding_stability → funding",      real_out, "NIH R01"),
    check("real: common_mismatch → mismatch",       real_out, "frequent structured guidance"),
    check("real: struggle_reason",                  real_out, "open-ended"),
    check("real: daily_experience",                 real_out, "morning"),
    check("real: outcome_expectations",             real_out, "2 first-author"),
]

all_ok = seed_ok and real_ok and all(checks)
print(f"\n{SEP}")
print(f"  SEED format : {'PASS' if seed_ok else 'FAIL'}")
print(f"  REAL format : {'PASS' if real_ok else 'FAIL'}")
print(f"  Spot-checks : {sum(checks)}/{len(checks)} passed")
print(f"  Overall     : {'PASS' if all_ok else 'FAIL'}")
print(SEP)
sys.exit(0 if all_ok else 1)
