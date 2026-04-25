import os
import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import MatchResult, PIProfile, StudentProfile
from schemas import (
    ChatRequest,
    ChatResponse,
    ChemistryReportSchema,
    MatchResultResponse,
    PIProfileResponse,
)
from scoring import (
    REPLY_LIKELIHOOD_SCORE,
    citizenship_mismatch,
    culture_fit_score,
    direct_connection,
    funding_stability_score,
    indirect_connection,
    location_passes_filter,
    mentorship_style_score,
    overall_score,
    predict_reply_likelihood,
    technical_skills_score,
)

# Make project root importable so agents/ package is accessible
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agents.research_match import score_research_fit  # noqa: E402
from agents.pi_avatar import build_pi_avatar          # noqa: E402
from agents.evaluator import evaluate_chemistry       # noqa: E402

import anthropic  # noqa: E402

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/match/{student_id}  — v1.0 matching
# ---------------------------------------------------------------------------

@router.post("/match/{student_id}", response_model=List[MatchResultResponse])
def run_matching(student_id: int, session: Session = Depends(get_session)):
    student = session.get(StudentProfile, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    pis = session.exec(select(PIProfile)).all()

    # Delete stale matches for this student
    old_matches = session.exec(
        select(MatchResult).where(MatchResult.student_id == student_id)
    ).all()
    for m in old_matches:
        session.delete(m)
    session.commit()

    results = []
    for pi in pis:
        # Pre-score location filter
        if not location_passes_filter(student, pi):
            continue

        # Research fit via Claude (highest priority)
        background = student.research_background or ""
        if student.cv_text:
            background += f"\n\nCV:\n{student.cv_text}"

        research_score, rationale = score_research_fit(
            background,
            pi.recent_abstracts or [],
            pi.research_areas or [],
        )

        # Deterministic scores
        mentorship = mentorship_style_score(student, pi)
        funding    = funding_stability_score(pi)
        skills     = technical_skills_score(student, pi)
        culture    = culture_fit_score(student, pi)
        reply_lik  = predict_reply_likelihood(pi)

        total = overall_score(research_score, mentorship, funding, skills, culture, reply_lik)

        # Connection detection
        is_direct = direct_connection(student, pi)
        is_indirect, via = indirect_connection(student, pi)
        if is_indirect:
            total = min(100.0, total + 10.0)

        # Flags
        c_mismatch = citizenship_mismatch(student, pi)

        match = MatchResult(
            student_id=student_id,
            pi_id=pi.id,
            research_direction_score=research_score,
            mentorship_style_score=mentorship,
            funding_stability_score=funding,
            culture_fit_score=culture,
            technical_skills_score=skills,
            location_score=100.0,
            is_direct_connection=is_direct,
            is_indirect_connection=is_indirect,
            indirect_connection_via=via,
            citizenship_mismatch=c_mismatch,
            research_match_rationale=rationale,
            reply_likelihood=reply_lik,
            overall_score=total,
        )
        session.add(match)
        results.append((match, pi))

    session.commit()
    for match, _ in results:
        session.refresh(match)

    # Sort: direct connections first, then by descending overall score
    results.sort(key=lambda x: (not x[0].is_direct_connection, -x[0].overall_score))

    output = []
    for match, pi in results:
        d = match.model_dump()
        d["pi"] = PIProfileResponse.model_validate(pi).model_dump()
        output.append(d)
    return output


# ---------------------------------------------------------------------------
# GET /api/matches/{student_id}  — retrieve existing matches
# ---------------------------------------------------------------------------

@router.get("/matches/{student_id}", response_model=List[MatchResultResponse])
def get_matches(student_id: int, session: Session = Depends(get_session)):
    matches = session.exec(
        select(MatchResult).where(MatchResult.student_id == student_id)
    ).all()

    output = []
    for match in matches:
        pi = session.get(PIProfile, match.pi_id)
        d = match.model_dump()
        if pi:
            d["pi"] = PIProfileResponse.model_validate(pi).model_dump()
        output.append(d)

    output.sort(key=lambda x: (not x["is_direct_connection"], -x["overall_score"]))
    return output


# ---------------------------------------------------------------------------
# GET /api/match/{match_id}  — fetch single match with PI data
# ---------------------------------------------------------------------------

@router.get("/match/{match_id}", response_model=MatchResultResponse)
def get_match(match_id: int, session: Session = Depends(get_session)):
    match = session.get(MatchResult, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    pi = session.get(PIProfile, match.pi_id)
    d = match.model_dump()
    if pi:
        d["pi"] = PIProfileResponse.model_validate(pi).model_dump()
    return d


# ---------------------------------------------------------------------------
# POST /api/simulate/{match_id}  — v2.0 PI avatar chat
# ---------------------------------------------------------------------------

@router.post("/simulate/{match_id}", response_model=ChatResponse)
def simulate_chat(
    match_id: int,
    request: ChatRequest,
    session: Session = Depends(get_session),
):
    match = session.get(MatchResult, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    pi = session.get(PIProfile, match.pi_id)
    if not pi:
        raise HTTPException(status_code=404, detail="PI not found")

    system_prompt = build_pi_avatar(pi)

    transcript: list = list(match.transcript or [])
    transcript.append({"role": "student", "content": request.message})

    # Convert to Claude message format (user = student, assistant = pi)
    messages = [
        {"role": "user" if t["role"] == "student" else "assistant", "content": t["content"]}
        for t in transcript
    ]

    pi_response = "I'm experiencing technical difficulties. Please try again shortly."
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=512,
                system=system_prompt,
                messages=messages,
            )
            pi_response = resp.content[0].text
        except Exception:
            pass  # keep fallback message

    transcript.append({"role": "pi", "content": pi_response})

    # Reassign (not mutate) to trigger SQLAlchemy change detection
    match.transcript = transcript
    session.add(match)
    session.commit()

    return ChatResponse(pi_response=pi_response, transcript=transcript, match_id=match_id)


# ---------------------------------------------------------------------------
# POST /api/evaluate/{match_id}  — v2.5 chemistry evaluation
# ---------------------------------------------------------------------------

@router.post("/evaluate/{match_id}", response_model=ChemistryReportSchema)
def evaluate_match(match_id: int, session: Session = Depends(get_session)):
    match = session.get(MatchResult, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if not match.transcript:
        raise HTTPException(
            status_code=400,
            detail="No transcript found. Run POST /simulate/{match_id} first.",
        )

    pi      = session.get(PIProfile, match.pi_id)
    student = session.get(StudentProfile, match.student_id)
    if not pi or not student:
        raise HTTPException(status_code=404, detail="PI or student record missing")

    report_obj = evaluate_chemistry(match.transcript, student, pi, match)
    report_dict = report_obj.model_dump()

    match.chemistry_report = report_dict
    session.add(match)
    session.commit()

    return report_dict


# ---------------------------------------------------------------------------
# GET /api/report/{match_id}  — fetch stored chemistry report
# ---------------------------------------------------------------------------

@router.get("/report/{match_id}")
def get_report(match_id: int, session: Session = Depends(get_session)):
    match = session.get(MatchResult, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if not match.chemistry_report:
        raise HTTPException(
            status_code=404,
            detail="No chemistry report yet. Run POST /evaluate/{match_id} first.",
        )

    pi = session.get(PIProfile, match.pi_id)
    match_data = match.model_dump()
    if pi:
        match_data["pi"] = PIProfileResponse.model_validate(pi).model_dump()
    return {
        "match": match_data,
        "report": match.chemistry_report,
    }
