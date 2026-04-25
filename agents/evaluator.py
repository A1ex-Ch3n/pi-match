from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING
from pydantic import BaseModel
import anthropic

if TYPE_CHECKING:
    from backend.models import StudentProfile, PIProfile, MatchResult

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


class ChemistryReport(BaseModel):
    overall_score: float
    dimension_scores: dict
    dimension_rationale: dict
    key_positives: list[str]
    key_concerns: list[str]
    recommended_questions: list[str]
    pi_introduction_draft: str


def evaluate_chemistry(
    transcript: list[dict],
    student_profile: "StudentProfile",
    pi_profile: "PIProfile",
    v1_match_result: "MatchResult",
) -> ChemistryReport:
    transcript_text = ""
    for turn in transcript:
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        label = "PI" if role == "pi" else "Student"
        transcript_text += f"{label}: {content}\n\n"

    student_summary = (
        f"Name: {student_profile.name}\n"
        f"Field: {student_profile.field_of_study}\n"
        f"Research Background: {student_profile.research_background}\n"
        f"Independence Preference (1=guided, 5=autonomous): {student_profile.independence_preference}\n"
        f"Intervention Tolerance (1=high PI involvement, 5=minimal): {student_profile.intervention_tolerance}\n"
        f"Meeting Frequency Preference (1=daily, 5=monthly): {student_profile.meeting_frequency_preference}\n"
        f"Work-Life Balance Importance: {student_profile.work_life_balance_importance}\n"
        f"Publication Rate Importance: {student_profile.publication_rate_importance}\n"
        f"Citizenship Status: {student_profile.citizenship_status}\n"
    )

    pi_summary = (
        f"Name: {pi_profile.name}\n"
        f"Institution: {pi_profile.institution}\n"
        f"Department: {pi_profile.department}\n"
        f"Research Areas: {', '.join(pi_profile.research_areas or [])}\n"
        f"Lab Size: {pi_profile.lab_size}\n"
        f"Funding Citizen Restricted: {pi_profile.funding_citizen_restricted}\n"
    )

    if pi_profile.pi_survey:
        pi_summary += f"PI Survey: {json.dumps(pi_profile.pi_survey)}\n"

    v1_summary = (
        f"V1 Research Direction Score: {v1_match_result.research_direction_score}\n"
        f"V1 Mentorship Style Score: {v1_match_result.mentorship_style_score}\n"
        f"V1 Overall Score: {v1_match_result.overall_score}\n"
    )

    prompt = f"""You are an objective evaluator assessing the chemistry between a PhD applicant and a PI based on their conversation transcript. You have NO prior context from the PI avatar — evaluate fresh from the transcript only.

## Student Profile
{student_summary}

## PI Profile
{pi_summary}

## V1 Match Scores (for reference only)
{v1_summary}

## Conversation Transcript
{transcript_text}

Evaluate the following 5 dimensions on a 0–100 scale:
1. research_alignment: How well do their research interests align based on the conversation?
2. mentorship_compatibility: Does the PI's mentorship style match the student's preferences?
3. culture_fit: Do their values around work, lab culture, and expectations align?
4. communication_fit: How well do they communicate — clarity, engagement, mutual understanding?
5. red_flags: Absence of red flags (100 = no red flags, 0 = serious concerns raised)

Also provide:
- key_positives: 2–3 specific transcript moments that demonstrate strong fit (quote or reference actual exchanges)
- key_concerns: 2–3 unresolved issues or mismatches surfaced in the conversation
- recommended_questions: 3–4 follow-up questions the student should ask the PI
- pi_introduction_draft: A warm, 3–4 sentence email the student could send to introduce themselves to this PI. Make it specific to the conversation and research overlap.

Compute overall_score as the weighted average:
  research_alignment * 0.35 + mentorship_compatibility * 0.25 + culture_fit * 0.20 + communication_fit * 0.15 + red_flags * 0.05

Respond ONLY with valid JSON matching this exact schema:
{{
  "overall_score": float,
  "dimension_scores": {{
    "research_alignment": float,
    "mentorship_compatibility": float,
    "culture_fit": float,
    "communication_fit": float,
    "red_flags": float
  }},
  "dimension_rationale": {{
    "research_alignment": "string",
    "mentorship_compatibility": "string",
    "culture_fit": "string",
    "communication_fit": "string",
    "red_flags": "string"
  }},
  "key_positives": ["string", "string"],
  "key_concerns": ["string", "string"],
  "recommended_questions": ["string", "string", "string"],
  "pi_introduction_draft": "string"
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return ChemistryReport(**data)
    except (json.JSONDecodeError, KeyError, ValueError):
        return ChemistryReport(
            overall_score=50.0,
            dimension_scores={
                "research_alignment": 50.0,
                "mentorship_compatibility": 50.0,
                "culture_fit": 50.0,
                "communication_fit": 50.0,
                "red_flags": 50.0,
            },
            dimension_rationale={
                "research_alignment": "Unable to evaluate from transcript.",
                "mentorship_compatibility": "Unable to evaluate from transcript.",
                "culture_fit": "Unable to evaluate from transcript.",
                "communication_fit": "Unable to evaluate from transcript.",
                "red_flags": "Unable to evaluate from transcript.",
            },
            key_positives=["Evaluation unavailable."],
            key_concerns=["Evaluation unavailable."],
            recommended_questions=["Please review the transcript manually."],
            pi_introduction_draft="Unable to generate introduction draft.",
        )
