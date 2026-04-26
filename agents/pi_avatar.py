from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Any, Optional

if TYPE_CHECKING:
    from agents.profile_builder import AvatarProfile


# ============================================================================
# Helper Functions for Survey Formatting
# ============================================================================

def _get(survey: Dict[str, Any], *keys: str) -> Optional[str]:
    """Return the first non-empty value found among the given keys."""
    for k in keys:
        v = survey.get(k)
        if v and str(v).strip():
            return str(v).strip()
    return None


def _format_pi_voice(pi_survey: Dict[str, Any]) -> str:
    """
    Build the PI's self-description section.
    Handles both hand-crafted seed format and real Google Form survey format.
    Produces richer output when more fields are available.
    """
    if not pi_survey:
        return ""

    sections = []

    # --- In the PI's own words: elevator pitch (highest priority) ---
    # seed: lab_description; real: lab_description_pitch
    pitch = _get(pi_survey, "lab_description_pitch", "lab_description")
    if pitch:
        sections.append(f'How I describe my lab: "{pitch}"')

    # --- Research direction ---
    research = _get(pi_survey, "research_priorities")
    if research and not research.startswith("TODO"):
        sections.append(f"Research direction: {research}")

    # --- Mentorship style ---
    style = _get(pi_survey, "mentorship_style")
    freq  = _get(pi_survey, "meeting_frequency")
    response_time = _get(pi_survey, "response_time")
    if style:
        line = f"Mentorship style: {style}"
        if freq:
            line += f" — meetings {freq}"
        if response_time:
            line += f" — email/Slack response: {response_time}"
        sections.append(line)

    # --- Autonomy and intervention levels (integers 1-5) ---
    _AUTONOMY_LABELS = {
        1: "highly guided — close direction on all tasks",
        2: "mostly guided — regular check-ins, limited self-direction",
        3: "moderately guided — balanced guidance and independence",
        4: "mostly autonomous — high independence, PI available when needed",
        5: "fully autonomous — student drives their own agenda",
    }
    _INTERVENTION_LABELS = {
        1: "very high — PI checks in constantly",
        2: "high — frequent PI involvement",
        3: "moderate — PI involved at key decision points",
        4: "low — students work independently, PI steps in when asked",
        5: "minimal — PI rarely intervenes unless escalated",
    }
    autonomy_raw = pi_survey.get("autonomy_style")
    if autonomy_raw is not None:
        try:
            n = int(autonomy_raw)
            sections.append(f"Independence expectation: {_AUTONOMY_LABELS.get(n, str(n))} ({n}/5)")
        except (ValueError, TypeError):
            pass

    intervention_raw = pi_survey.get("intervention_level")
    if intervention_raw is not None:
        try:
            n = int(intervention_raw)
            sections.append(f"PI involvement level: {_INTERVENTION_LABELS.get(n, str(n))} ({n}/5)")
        except (ValueError, TypeError):
            pass

    # --- Lab expectations / outcomes ---
    expectations = _get(pi_survey, "lab_expectations", "outcome_expectations")
    if expectations:
        sections.append(f"Lab expectations: {expectations}")

    # --- What makes students succeed ---
    # seed: success_traits; real: successful_student_description
    success_desc = _get(pi_survey, "successful_student_description", "success_traits")
    qualities    = _get(pi_survey, "student_qualities")
    if success_desc:
        sections.append(f"What distinguishes my best students: {success_desc}")
    if qualities:
        sections.append(f"What I look for in students: {qualities}")

    # --- Poor fit signals ---
    poor_fit = _get(pi_survey, "poor_fit_traits")
    if poor_fit:
        sections.append(f"Poor fit traits: {poor_fit}")

    # --- How I respond when a student is struggling ---
    # seed: student_support; real: struggle_response
    struggle_resp = _get(pi_survey, "struggle_response", "student_support")
    if struggle_resp:
        sections.append(f"When a student is struggling: {struggle_resp}")

    # --- Common reason students struggle or leave ---
    struggle_reason = _get(pi_survey, "struggle_reason")
    if struggle_reason:
        sections.append(f"Common struggle reason: {struggle_reason}")

    # --- Day-to-day experience in the lab ---
    daily = _get(pi_survey, "daily_experience")
    if daily:
        sections.append(f"Day-to-day in my lab: {daily}")

    # --- Project assignment and working style ---
    project_assign = _get(pi_survey, "project_assignment")
    # seed: work_pattern; real: working_pattern; both also have working_style
    working_style  = _get(pi_survey, "working_style", "working_pattern", "work_pattern")
    lab_tone       = _get(pi_survey, "lab_tone", "lab_environment")
    if project_assign:
        sections.append(f"How projects are assigned: {project_assign}")
    if working_style:
        sections.append(f"Working style: {working_style}")
    if lab_tone:
        sections.append(f"Lab tone: {lab_tone}")

    # --- Work-life balance ---
    _WLB_LABELS = {
        1: "not a priority — lab moves fast, long hours expected",
        2: "somewhat supported — hustle culture but not extreme",
        3: "neutral — neither pushed nor discouraged",
        4: "encouraged — PI actively supports healthy boundaries",
        5: "strongly encouraged — work-life balance is an explicit lab value",
    }
    wlb_raw = pi_survey.get("work_life_balance")
    if wlb_raw is not None:
        try:
            n = int(wlb_raw)
            sections.append(f"Work-life balance stance: {_WLB_LABELS.get(n, str(n))} ({n}/5)")
        except (ValueError, TypeError):
            wlb_text = str(wlb_raw).strip()
            if wlb_text:
                sections.append(f"Work-life balance: {wlb_text}")

    # --- Graduation timeline ---
    # seed: graduation_timeline; real: time_to_graduation
    timeline = _get(pi_survey, "graduation_timeline", "time_to_graduation")
    if timeline:
        sections.append(f"Typical time to graduation: {timeline}")

    # --- Funding ---
    funding_src  = _get(pi_survey, "funding_source")
    funding_stab = _get(pi_survey, "funding_stability", "funding_stability_text")
    funding_note = _get(pi_survey, "funding_note")
    if funding_src or funding_stab:
        parts = [p for p in [funding_src, funding_stab] if p]
        sections.append("Funding: " + " — ".join(parts))
    if funding_note:
        sections.append(f"Funding note: {funding_note}")

    # --- Additional notes ---
    notes = _get(pi_survey, "additional_notes")
    if notes and notes.lower() not in ("i think everything was mostly covered", "n/a", ""):
        sections.append(f"Additional notes: {notes}")

    # --- Common mismatch (for honest framing) ---
    # seed: critical_mismatch; real: common_mismatch
    mismatch = _get(pi_survey, "common_mismatch", "critical_mismatch")
    if mismatch:
        sections.append(f"Common student–lab mismatch: {mismatch}")

    if not sections:
        return ""

    return "\n".join(f"  - {s}" for s in sections)


def _format_student_voice(student_responses: List[Dict[str, Any]]) -> str:
    """
    Format anonymous student survey responses into a coherent picture.
    Handles both hand-crafted and real survey formats.
    Surfaces gaps between PI self-description and lived reality.
    """
    if not student_responses:
        return ""

    count = len(student_responses)

    # Collect values across all responses for each theme
    def collect(key: str) -> List[str]:
        return [r[key] for r in student_responses if r.get(key, "").strip()]

    # Priority fields — show if any response has them
    themes: List[tuple[str, List[str]]] = [
        ("Overall experience",         collect("overall_experience")),
        ("Mentorship in practice",      collect("mentorship_reality") or collect("mentorship")),
        ("Work-life balance reality",   collect("work_life_balance_reality") or collect("work_life_balance")),
        ("Lab culture",                 collect("lab_culture")),
        ("Demand level",                collect("demanding_level")),
        ("PI vs reality gap",           collect("pi_vs_reality_detail") or collect("pi_vs_reality")),
        ("What students wish they knew", collect("wish_knew")),
        ("Who tends to succeed",        collect("success_profile")),
        ("Who tends to struggle",       collect("struggle_profile")),
        ("Publication rate",            collect("publication_rate")),
    ]

    output = [f"What current lab members report (from {count} anonymous response(s)):"]
    for label, values in themes:
        if not values:
            continue
        if len(values) == 1:
            output.append(f"  - {label}: {values[0]}")
        else:
            # Multiple responses — show all as sub-bullets if they differ
            unique = list(dict.fromkeys(values))  # deduplicate, preserve order
            if len(unique) == 1:
                output.append(f"  - {label}: {unique[0]}")
            else:
                output.append(f"  - {label}:")
                for v in unique:
                    output.append(f"      • {v}")

    return "\n".join(output)


# ============================================================================
# Main Avatar Builder
# ============================================================================

def build_pi_avatar(avatar_profile: "AvatarProfile") -> str:
    name = avatar_profile.name
    institution = avatar_profile.institution
    department = avatar_profile.department
    research_areas = ", ".join(avatar_profile.research_areas or [])

    abstracts_section = ""
    for i, abstract in enumerate(avatar_profile.recent_abstracts or []):
        abstracts_section += f"\nPaper {i+1}: {abstract}"

    grants_section = ""
    for grant in avatar_profile.nsf_grants or []:
        title = grant.get("title", "Untitled")
        amount = grant.get("amount") or grant.get("fundsObligatedAmt", "N/A")
        expiry = grant.get("expiry_date") or grant.get("expDate", "N/A")
        citizen_only = grant.get("citizen_only", False)
        citizen_note = " (US citizen/PR required)" if citizen_only else ""
        grants_section += f"\n- {title}: ${amount}, expires {expiry}{citizen_note}"

    if not grants_section:
        grants_section = "\nNo NSF grants on record."

    lab_size = avatar_profile.lab_size or "unknown"
    is_recruiting = "Yes" if avatar_profile.is_recruiting else "No"

    # =========================================================================
    # Build survey sections based on pipeline_type
    # =========================================================================

    from agents.profile_builder import PipelineType

    pipeline_type = avatar_profile.pipeline_type
    pi_voice_section = ""
    student_voice_section = ""
    honest_uncertainty = ""

    if pipeline_type == PipelineType.PI_AND_STUDENT:
        pi_voice_section = "\n\n## My Perspective (from my own survey responses)"
        pi_formatted = _format_pi_voice(avatar_profile.pi_survey)
        if pi_formatted:
            pi_voice_section += "\n" + pi_formatted

        student_voice_section = "\n\n## What Current Lab Members Report (anonymous)"
        student_formatted = _format_student_voice(avatar_profile.student_survey_responses)
        if student_formatted:
            student_voice_section += "\n" + student_formatted
        student_voice_section += (
            "\n\nIMPORTANT: You are aware of this student perspective. When relevant, "
            "you may acknowledge these themes honestly — e.g. 'Students have noted that...'. "
            "Never attribute responses to individuals."
        )

    elif pipeline_type == PipelineType.PI_ONLY:
        pi_voice_section = "\n\n## My Perspective (from my own survey responses)"
        pi_formatted = _format_pi_voice(avatar_profile.pi_survey)
        if pi_formatted:
            pi_voice_section += "\n" + pi_formatted

    else:  # PUBLIC_ONLY
        honest_uncertainty = (
            "\n\nNote: You don't have detailed lab culture or mentorship survey data. "
            "Draw only on the research profile above. When asked about lab culture or "
            "mentorship style, acknowledge uncertainty and invite the applicant to ask directly."
        )

    # Build numbered paper list (url is optional — east/west PIs don't have it)
    papers_list = avatar_profile.papers or []
    if papers_list:
        def _fmt_paper(i: int, p: dict) -> str:
            title  = p.get("title", "Untitled")
            year   = str(p.get("year", "")).strip()
            venue  = str(p.get("venue", "")).strip()
            url    = p.get("url", "")
            link   = f"[{title}]({url})" if url else title
            suffix = f"{venue} {year}".strip(" —")
            return f"{i+1}. {link}" + (f" — {suffix}" if suffix else "")

        papers_section = "\n".join(_fmt_paper(i, p) for i, p in enumerate(papers_list))
    else:
        papers_section = "No papers listed. Discuss research directions from the abstracts above."

    system_prompt = f"""## IDENTITY (CRITICAL — NEVER CONTRADICT)
You are Professor {name}.
Institution: {institution}
Department: {department}
You are NOT at any other university. If asked, you are at {institution}. This is non-negotiable.

---

You are roleplaying as Professor {name}, speaking with a PhD applicant considering your lab.
Your goal: have a genuine, informative conversation — help them understand your lab and assess their fit.

## Research
You work on: {research_areas}

Recent work from your lab:{abstracts_section}

## Lab Overview
- Lab size: ~{lab_size} members
- Currently recruiting: {is_recruiting}

## Funding
{grants_section}
{pi_voice_section}{student_voice_section}{honest_uncertainty}

## Papers (ONLY cite these — never fabricate titles or links)
{papers_section}

## Conversation Rules
- Speak in first person as Professor {name}. You ARE this professor.
- Be specific — reference your actual papers and research directions above.
- When mentioning a paper, write its title in **bold** exactly as it appears in the list above. Do NOT write URLs or markdown links — the system will add links automatically.
- NEVER invent paper titles, grants, or lab details not listed above.
- Ask the applicant exactly ONE question per response about their fit.
- If uncertain about something not in your profile, say so: "I'd want you to ask me that directly."
- Keep responses focused and conversational — 3–5 sentences plus your one question.
- You are evaluating the applicant just as they are evaluating you.
"""

    return system_prompt
