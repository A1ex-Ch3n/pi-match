"""
Scoring helpers for v1.0 matching. All agent Claude calls are delegated to
agents/ — this module handles deterministic score computation only.
"""
from typing import Optional, Tuple

SCORE_WEIGHTS = {
    "research_direction": 0.40,
    "mentorship_style":   0.20,
    "funding_stability":  0.15,
    "technical_skills":   0.10,
    "culture_fit":        0.10,
    "reply_likelihood":   0.05,
}

REPLY_LIKELIHOOD_SCORE = {"high": 100.0, "medium": 60.0, "low": 30.0}

_WEST_COAST  = {"CA", "OR", "WA"}
_EAST_COAST  = {"NY", "MA", "MD", "CT", "NJ", "PA", "VA", "NC", "FL", "DC"}
_MIDWEST     = {"IL", "OH", "MI", "MN", "WI", "IN", "MO", "IA"}
_LOCATION_MAP = {
    "west_coast": _WEST_COAST,
    "east_coast": _EAST_COAST,
    "midwest":    _MIDWEST,
}


def location_passes_filter(student, pi) -> bool:
    pref = student.location_preference
    # Handle both old str format and new List[str] format
    if not pref:
        return True
    if isinstance(pref, str):
        prefs = [pref]
    else:
        prefs = list(pref)
    if not prefs or "any" in prefs:
        return True
    return any(pi.location in _LOCATION_MAP.get(p, set()) for p in prefs)


def citizenship_mismatch(student, pi) -> bool:
    if not pi.funding_citizen_restricted:
        return False
    return student.citizenship_status not in ("us_citizen", "pr")


def direct_connection(student, pi) -> bool:
    known = {n.lower().strip() for n in (student.known_professors or [])}
    return pi.name.lower().strip() in known


def indirect_connection(student, pi) -> Tuple[bool, Optional[str]]:
    known = [n.lower().strip() for n in (student.known_professors or [])]
    co_names = pi.co_author_names or []
    for coauthor in co_names:
        coauthor_lower = coauthor.lower().strip()
        for prof in known:
            # Skip if it's the PI themselves (already counted as direct)
            if prof == pi.name.lower().strip():
                continue
            if prof in coauthor_lower or coauthor_lower in prof:
                return True, coauthor
    return False, None


def _safe_int(val, default: int = 3) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def mentorship_style_score(student, pi) -> float:
    survey = pi.pi_survey or {}
    if not survey:
        return 50.0

    score = 50.0

    pi_autonomy = _safe_int(survey.get("autonomy_style", survey.get("mentorship_style", 3)))
    diff = abs(pi_autonomy - _safe_int(student.independence_preference))
    score += (2 - diff) * 10          # ±20 pts

    pi_meeting = _safe_int(survey.get("meeting_frequency_num", survey.get("meeting_frequency", 3)))
    diff = abs(pi_meeting - _safe_int(student.meeting_frequency_preference))
    score += (2 - diff) * 8           # ±16 pts

    pi_involvement = _safe_int(survey.get("intervention_level", survey.get("involvement", 3)))
    diff = abs(pi_involvement - _safe_int(student.intervention_tolerance))
    score += (2 - diff) * 7           # ±14 pts

    return max(0.0, min(100.0, score))


def funding_stability_score(pi) -> float:
    score = 0.0
    if pi.has_active_nsf_grant:
        score += 50.0
    funding = pi.total_active_funding_usd or 0
    if funding >= 500_000:
        score += 30.0
    elif funding >= 200_000:
        score += 20.0
    elif funding >= 50_000:
        score += 10.0
    if pi.is_recruiting:
        score += 20.0
    return min(100.0, score)


def technical_skills_score(student, pi) -> float:
    skills = [s.lower() for s in (student.technical_skills or [])]
    areas  = [a.lower() for a in (pi.research_areas or [])]
    if not skills or not areas:
        return 50.0
    matches = sum(
        1 for s in skills
        if any(s in a or a in s for a in areas)
    )
    return min(100.0, (matches / len(skills)) * 100 + 20)


def culture_fit_score(student, pi) -> float:
    score = 50.0
    lab_size = pi.lab_size or 5
    pref = student.preferred_lab_size

    if pref == "small"  and lab_size <= 4:   score += 25.0
    elif pref == "small"  and lab_size <= 8:  score += 10.0
    elif pref == "medium" and 5 <= lab_size <= 12: score += 25.0
    elif pref == "medium" and lab_size <= 15: score += 10.0
    elif pref == "large"  and lab_size > 10:  score += 25.0
    elif pref == "any":                        score += 15.0

    survey = pi.pi_survey or {}
    if survey:
        pi_wlb = _safe_int(survey.get("work_life_balance", 3))
        diff = abs(pi_wlb - _safe_int(student.work_life_balance_importance))
        score += max(0, (2 - diff) * 10)

    return min(100.0, score)


def predict_reply_likelihood(pi) -> str:
    papers = pi.papers_last_12_months or 0
    if papers >= 4:
        return "high"
    if papers >= 2:
        return "medium"
    return "low"


def overall_score(
    research: float,
    mentorship: float,
    funding: float,
    skills: float,
    culture: float,
    reply: str,
) -> float:
    reply_score = REPLY_LIKELIHOOD_SCORE.get(reply, 60.0)
    return (
        research   * SCORE_WEIGHTS["research_direction"] +
        mentorship * SCORE_WEIGHTS["mentorship_style"]   +
        funding    * SCORE_WEIGHTS["funding_stability"]  +
        skills     * SCORE_WEIGHTS["technical_skills"]   +
        culture    * SCORE_WEIGHTS["culture_fit"]        +
        reply_score * SCORE_WEIGHTS["reply_likelihood"]
    )
