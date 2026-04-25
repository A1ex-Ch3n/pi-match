from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models import PIProfile


def build_pi_avatar(pi_profile: "PIProfile") -> str:
    name = pi_profile.name
    institution = pi_profile.institution
    department = pi_profile.department
    research_areas = ", ".join(pi_profile.research_areas or [])

    abstracts_section = ""
    for i, abstract in enumerate(pi_profile.recent_abstracts or []):
        abstracts_section += f"\nPaper {i+1}: {abstract}"

    grants_section = ""
    for grant in pi_profile.nsf_grants or []:
        title = grant.get("title", "Untitled")
        amount = grant.get("amount") or grant.get("fundsObligatedAmt", "N/A")
        expiry = grant.get("expiry_date") or grant.get("expDate", "N/A")
        citizen_only = grant.get("citizen_only", False)
        citizen_note = " (US citizen/PR required)" if citizen_only else ""
        grants_section += f"\n- {title}: ${amount}, expires {expiry}{citizen_note}"

    if not grants_section:
        grants_section = "\nNo NSF grants on record."

    lab_size = pi_profile.lab_size or "unknown"
    is_recruiting = "Yes" if pi_profile.is_recruiting else "No"

    pi_survey_section = ""
    if pi_profile.pi_survey:
        pi_survey_section = "\n\nPI Survey Responses (your own voice):\n"
        for key, value in pi_profile.pi_survey.items():
            pi_survey_section += f"  {key}: {value}\n"

    student_responses_section = ""
    if pi_profile.student_survey_responses:
        student_responses_section = (
            "\n\nAnonymous Current Student Perspectives (do not attribute to individuals):\n"
        )
        for resp in pi_profile.student_survey_responses:
            for key, value in resp.items():
                student_responses_section += f"  - {key}: {value}\n"
            student_responses_section += "\n"

    system_prompt = f"""You are Professor {name}, a faculty member in the {department} at {institution}.

## Your Research
You work on: {research_areas}

Recent papers from your lab:{abstracts_section}

## Your Lab
- Lab size: approximately {lab_size} members
- Currently recruiting: {is_recruiting}

## Funding
Active NSF grants:{grants_section}
{pi_survey_section}{student_responses_section}

## How You Behave in This Conversation
- Speak in first person as Professor {name}. You ARE this professor.
- Be specific — reference your actual papers, grants, and research directions above.
- Ask the applicant exactly ONE question per response about their fit for your lab.
- Surface what you care about most based on your survey responses above.
- If you are uncertain about something not covered in your profile, say so honestly — for example: "I'm not certain about that — you'd want to ask me directly."
- Never fabricate details about your research, funding, or lab culture that are not provided above.
- Keep responses focused and conversational (3–5 sentences plus your one question).
- You are evaluating whether this applicant is a good fit, just as they are evaluating you.
"""

    return system_prompt
