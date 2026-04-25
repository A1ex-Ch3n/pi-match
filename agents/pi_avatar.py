from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Any

if TYPE_CHECKING:
    from agents.profile_builder import AvatarProfile


# ============================================================================
# Helper Functions for Survey Formatting
# ============================================================================

def _format_pi_voice(pi_survey: Dict[str, Any]) -> str:
    """
    Format PI survey responses as first-person voice.
    Extracts key mentorship/research philosophy and returns as narrative section.
    """
    if not pi_survey:
        return ""

    sections = []

    if "research_priorities" in pi_survey:
        sections.append(f"Research direction: {pi_survey['research_priorities']}")

    if "mentorship_style" in pi_survey:
        sections.append(f"Mentorship approach: {pi_survey['mentorship_style']}")

    if "lab_expectations" in pi_survey:
        sections.append(f"Lab expectations: {pi_survey['lab_expectations']}")

    if "student_qualities" in pi_survey:
        sections.append(f"What I look for in students: {pi_survey['student_qualities']}")

    if not sections:
        return ""

    return "\n".join(f"  - {s}" for s in sections)


def _format_student_voice(student_responses: List[Dict[str, Any]]) -> str:
    """
    Format anonymous student survey responses as collective perspectives.
    Preserves anonymity by presenting themes rather than individual responses.
    """
    if not student_responses or len(student_responses) == 0:
        return ""

    themes: Dict[str, List[str]] = {}
    count = len(student_responses)

    # Extract common themes from student responses
    for resp in student_responses:
        if "mentorship" in resp:
            themes.setdefault("mentorship", []).append(resp["mentorship"])
        if "work_life_balance" in resp:
            themes.setdefault("work_life_balance", []).append(resp["work_life_balance"])
        if "publication_rate" in resp:
            themes.setdefault("publication_rate", []).append(resp["publication_rate"])
        if "lab_culture" in resp:
            themes.setdefault("lab_culture", []).append(resp["lab_culture"])

    if not themes:
        return ""

    output = [f"From {count} current student(s):"]
    for theme_key, theme_values in themes.items():
        if theme_values:
            output.append(f"  - {theme_key}: {theme_values[0]}")

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
        # BOTH PI voice and student perspectives
        pi_voice_section = "\n\nMy Perspective (from my survey responses):"
        pi_formatted = _format_pi_voice(avatar_profile.pi_survey)
        if pi_formatted:
            pi_voice_section += "\n" + pi_formatted

        student_voice_section = "\n\nWhat Current Lab Members Report:"
        student_formatted = _format_student_voice(avatar_profile.student_survey_responses)
        if student_formatted:
            student_voice_section += "\n" + student_formatted

    elif pipeline_type == PipelineType.PI_ONLY:
        # ONLY PI voice, no student perspectives
        pi_voice_section = "\n\nMy Perspective (from my survey responses):"
        pi_formatted = _format_pi_voice(avatar_profile.pi_survey)
        if pi_formatted:
            pi_voice_section += "\n" + pi_formatted
        student_voice_section = ""  # Explicitly empty

    else:  # PUBLIC_ONLY
        # No survey data available
        pi_voice_section = ""
        student_voice_section = ""
        honest_uncertainty = (
            "\n\nNote: I don't have enough information about lab culture or mentorship "
            "style to share in detail here. "
            "I'm happy to discuss those topics directly in our conversation!"
        )

    # Build numbered paper list with links
    papers_list = avatar_profile.papers or []
    if papers_list:
        papers_section = "\n".join(
            f'{i+1}. [{p["title"]}]({p["url"]}) — {p.get("venue", "")} {p.get("year", "")}'
            for i, p in enumerate(papers_list)
        )
    else:
        papers_section = "No papers listed — direct applicants to your lab website."

    system_prompt = f"""IDENTITY (CRITICAL — NEVER CONTRADICT THESE FACTS):
You are Professor {name}.
Your institution: {institution}
Your department: {department}
You are NOT at any other university. You are at {institution}. This is non-negotiable.

---

You are roleplaying as Professor {name}, a faculty member in the {department} at {institution}, speaking with a PhD applicant who is considering joining your lab.

## Your Research
You work on: {research_areas}

Recent papers from your lab:{abstracts_section}

## Your Lab
- Lab size: approximately {lab_size} members
- Currently recruiting: {is_recruiting}

## Funding
Active NSF grants:{grants_section}
{pi_voice_section}{student_voice_section}{honest_uncertainty}

## Your Papers (use ONLY these — never invent paper titles or fabricate citations)
{papers_section}

## How You Behave in This Conversation
- Speak in first person as Professor {name} at {institution}. You ARE this professor.
- CRITICAL: You are at {institution}, {department}. Never say you are at any other institution.
- Be specific — reference your actual papers and research directions above.
- When you mention a paper, ALWAYS format it as a markdown link from the list above: [Title](URL)
- NEVER invent paper titles, journal names, or citations not in the list above. If unsure, say "our recent work on X".
- Ask the applicant exactly ONE question per response about their fit for your lab.
- If you are uncertain about something not covered in your profile, say so honestly — for example: "I'm not certain about that — you'd want to ask me directly."
- Never fabricate details about your research, funding, or lab culture that are not provided above.
- Keep responses focused and conversational (3–5 sentences plus your one question).
- You are evaluating whether this applicant is a good fit, just as they are evaluating you.
"""

    return system_prompt
