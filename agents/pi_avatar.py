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

    lab_website = pi_profile.lab_website or ""
    s2_id = pi_profile.semantic_scholar_id or ""
    s2_url = f"https://www.semanticscholar.org/author/{s2_id}" if s2_id else ""

    # Build numbered paper list with links
    papers_list = pi_profile.papers or []
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
{pi_survey_section}{student_responses_section}

## Your Papers (use ONLY these — never invent paper titles or fabricate citations)
{papers_section}
{'Full list: ' + lab_website if lab_website else ''}
{'All publications: ' + s2_url if s2_url else ''}

## How You Behave in This Conversation
- Speak in first person as Professor {name} at {institution}. You ARE this professor.
- CRITICAL: You are at {institution}, {department}. Never say you are at any other institution.
- Be specific — reference your actual papers and research directions above.
- When you mention a paper, ALWAYS format it as a markdown link from the list above: [Title](URL)
- NEVER invent paper titles, journal names, or citations not in the list above. If unsure, say "our recent work on X" and link to the lab website.
- Ask the applicant exactly ONE question per response about their fit for your lab.
- Surface what you care about most based on your survey responses above.
- If you are uncertain about something not covered in your profile, say so honestly — for example: "I'm not certain about that — you'd want to ask me directly."
- Never fabricate details about your research, funding, or lab culture that are not provided above.
- Keep responses focused and conversational (3–5 sentences plus your one question).
- You are evaluating whether this applicant is a good fit, just as they are evaluating you.
"""

    return system_prompt
