import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

log = logging.getLogger("pimatch.matching")

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import MatchResult, PIProfile, StudentProfile
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ChemistryReportSchema,
    MatchResultResponse,
    PIProfileResponse,
)
from backend.scoring import (
    REPLY_LIKELIHOOD_SCORE,
    RESEARCH_MIN_SCORE,
    SCORE_WEIGHTS,
    citizenship_mismatch,
    culture_fit_score,
    department_passes_filter,
    direct_connection,
    funding_stability_score,
    has_keyword_overlap,
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
from agents.profile_builder import build_avatar_profile  # noqa: E402
from agents.pi_avatar import build_pi_avatar          # noqa: E402
from agents.evaluator import evaluate_chemistry       # noqa: E402

import anthropic  # noqa: E402

router = APIRouter()

# Shortlist size: PIs that pass stage-1 deterministic pre-scoring and proceed
# to the Claude research-fit call. Direct/indirect connections are always forced
# in on top of this cap.
_SHORTLIST_SIZE = 75

# Tracks the shortlist size per student so match_progress can report accurate
# totals even while Claude calls are still running.
_shortlist_sizes: dict[int, int] = {}


# ---------------------------------------------------------------------------
# POST /api/match/{student_id}  — v1.0 matching (two-stage pipeline)
# ---------------------------------------------------------------------------

@router.post("/match/{student_id}", response_model=List[MatchResultResponse])
def run_matching(student_id: int, session: Session = Depends(get_session)):
    t_start = time.time()

    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Set it in your .env file and restart the server before running matching.",
        )

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

    background = student.research_background or ""
    if student.cv_text:
        background += f"\n\nCV:\n{student.cv_text}"

    # ── Logging header ────────────────────────────────────────────────────────
    pfx = f"[MATCH #{student_id}]"
    log.info("%s === %s | loc=%s | field=%s ===",
             pfx, student.name,
             ",".join(student.location_preference or ["any"]),
             student.field_category or "any")
    log.info("%s   Topics : %s", pfx, ", ".join(student.preferred_research_topics or []) or "(none)")
    log.info("%s   Skills : %s", pfx, ", ".join(student.technical_skills or []) or "(none)")
    log.info("%s   Background: %.120s%s", pfx,
             student.research_background or "",
             "…" if len(student.research_background or "") > 120 else "")

    # ── Location + department filter ──────────────────────────────────────────
    eligible = [
        pi for pi in pis
        if location_passes_filter(student, pi) and department_passes_filter(student, pi)
    ]
    log.info("%s Filter: %d total PIs → %d eligible (location+dept)", pfx, len(pis), len(eligible))
    if not eligible:
        log.info("%s No eligible PIs — returning empty results", pfx)
        return []

    # ── Stage 1: deterministic pre-score (no Claude, ~50 ms) ─────────────────
    # Only research-relevant signals: technical skills (best proxy for research
    # fit) and funding (student needs a funded lab). Culture/reply excluded —
    # they have nothing to do with whether the PI's research aligns.
    # Keyword overlap adds +15 so topic-matched PIs rank above equally-skilled
    # ones with no shared terminology.
    def _det_score(pi: PIProfile) -> float:
        skills   = technical_skills_score(student, pi)
        funding  = funding_stability_score(pi)
        kw_bonus = 15.0 if has_keyword_overlap(student, pi) else 0.0
        return skills * 0.75 + funding * 0.25 + kw_bonus

    forced_ids: set[int] = set()
    forced_labels: dict[int, str] = {}
    for pi in eligible:
        if direct_connection(student, pi):
            forced_ids.add(pi.id)
            forced_labels[pi.id] = "direct"
        elif indirect_connection(student, pi)[0]:
            forced_ids.add(pi.id)
            forced_labels[pi.id] = "indirect"

    det_sorted = sorted(
        (pi for pi in eligible if pi.id not in forced_ids),
        key=_det_score,
        reverse=True,
    )
    remaining_slots = max(0, _SHORTLIST_SIZE - len(forced_ids))
    shortlist_ids = forced_ids | {pi.id for pi in det_sorted[:remaining_slots]}
    shortlist = [pi for pi in eligible if pi.id in shortlist_ids]

    log.info("%s Stage 1: %d connections forced | shortlist=%d / %d eligible",
             pfx, len(forced_ids), len(shortlist), len(eligible))

    if forced_ids:
        for pi in eligible:
            if pi.id in forced_ids:
                log.info("%s   FORCED (%s): %s [%s]",
                         pfx, forced_labels[pi.id], pi.name, pi.institution)

    log.info("%s Stage 1 top 10 by deterministic score:", pfx)
    for pi in det_sorted[:10]:
        ds = _det_score(pi)
        kw = "kw✓" if has_keyword_overlap(student, pi) else "kw✗"
        log.info("%s   %5.1f  %-35s [%-22s] %s",
                 pfx, ds, pi.name, pi.institution, kw)

    _shortlist_sizes[student_id] = len(shortlist)

    # ── Stage 2: keyword pre-filter + Claude research-fit on shortlist ────────
    log.info("%s Stage 2: scoring %d shortlisted PIs (8 workers) …", pfx, len(shortlist))

    def _score_pi(pi: PIProfile):
        if not has_keyword_overlap(student, pi):
            return pi.id, 30.0, "No keyword overlap with student's research background."
        paper_titles = [p["title"] for p in (pi.papers or []) if p.get("title")]
        score, rationale = score_research_fit(
            background,
            pi.recent_abstracts or [],
            pi.research_areas or [],
            pi_paper_titles=paper_titles or None,
        )
        return pi.id, score, rationale

    # ── Phase 1: fire all Claude calls, collect raw results in memory ────────
    # No DB writes yet — we need all scores before we can compute the run mean.
    raw: dict[int, tuple[float, str]] = {}   # pi_id → (score, rationale)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_score_pi, pi): pi for pi in shortlist}
        for future in as_completed(futures):
            pi = futures[future]
            pi_id, score, rationale = future.result()
            raw[pi_id] = (score, rationale)

    # ── Mean fallback: replace neutral 50s with the run's real-score average ─
    def _is_fallback(rationale: str) -> bool:
        return "defaulting to neutral" in rationale or "Unable to compute" in rationale

    real_scores = [s for s, r in raw.values()
                   if not r.startswith("No keyword overlap") and not _is_fallback(r)]
    run_mean = sum(real_scores) / len(real_scores) if real_scores else 50.0
    mean_rationale = (
        f"Research fit estimated at run average ({run_mean:.0f}) — "
        f"no abstract or paper data available for precise scoring."
    )
    log.info("%s Run mean research score: %.1f  (from %d real Claude scores)",
             pfx, run_mean, len(real_scores))

    adjusted: dict[int, tuple[float, str]] = {}
    for pi_id, (score, rationale) in raw.items():
        if _is_fallback(rationale):
            adjusted[pi_id] = (run_mean, mean_rationale)
        else:
            adjusted[pi_id] = (score, rationale)

    # ── Phase 2: apply gate, score deterministically, commit to DB ────────────
    results      = []
    dropped_gate = 0
    dropped_kw   = 0
    pi_by_id     = {pi.id: pi for pi in shortlist}

    for pi_id, (research_score, rationale) in adjusted.items():
        pi = pi_by_id[pi_id]

        if rationale.startswith("No keyword overlap"):
            src = "KW-SKIP "
        elif rationale.startswith("Research fit estimated at run average"):
            src = "MEAN-FB "
        else:
            src = "CLAUDE  "

        if research_score < RESEARCH_MIN_SCORE:
            _shortlist_sizes[student_id] = max(0, _shortlist_sizes.get(student_id, 1) - 1)
            log.info("%s   [%s] %-35s R=%4.0f → DROPPED (< %.0f)",
                     pfx, src, pi.name, research_score, RESEARCH_MIN_SCORE)
            if src == "KW-SKIP ":
                dropped_kw += 1
            else:
                dropped_gate += 1
            continue

        mentorship = mentorship_style_score(student, pi)
        funding    = funding_stability_score(pi)
        skills     = technical_skills_score(student, pi)
        culture    = culture_fit_score(student, pi)
        reply_lik  = predict_reply_likelihood(pi)

        total = overall_score(research_score, mentorship, funding, skills, culture, reply_lik)

        is_direct = direct_connection(student, pi)
        is_indirect, via = indirect_connection(student, pi)
        conn_tag = ""
        if is_direct:
            conn_tag = " 🤝direct"
        elif is_indirect:
            conn_tag = f" 🔗via {via}"
            total = min(100.0, total + 10.0)

        c_mismatch = citizenship_mismatch(student, pi)
        citizen_tag = " 🇺🇸" if c_mismatch else ""

        log.info(
            "%s   [%s] %-35s R=%4.0f M=%3.0f F=%3.0f S=%3.0f C=%3.0f"
            " reply=%-3s → %5.1f%s%s",
            pfx, src, pi.name,
            research_score, mentorship, funding, skills, culture,
            reply_lik, total, conn_tag, citizen_tag,
        )

        match = MatchResult(
            student_id=student_id,
            pi_id=pi_id,
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
        session.commit()
        session.refresh(match)
        results.append((match, pi))

    # Sort: direct connections first, then descending overall score
    results.sort(key=lambda x: (not x[0].is_direct_connection, -x[0].overall_score))

    # ── Results summary ───────────────────────────────────────────────────────
    log.info("%s Results: %d matches | %d kw-dropped | %d gate-dropped | %.1fs elapsed",
             pfx, len(results), dropped_kw, dropped_gate, time.time() - t_start)
    log.info("%s Top 15 matches:", pfx)
    for rank, (match, pi) in enumerate(results[:15], 1):
        conn = ""
        if match.is_direct_connection:
            conn = " [DIRECT]"
        elif match.is_indirect_connection:
            conn = f" [via {match.indirect_connection_via}]"
        citizen = " [🇺🇸]" if match.citizenship_mismatch else ""
        log.info(
            "%s   #%-2d %5.1f  %-35s R=%4.0f M=%3.0f F=%3.0f S=%3.0f C=%3.0f%s%s",
            pfx, rank, match.overall_score, pi.name,
            match.research_direction_score,
            match.mentorship_style_score,
            match.funding_stability_score,
            match.technical_skills_score,
            match.culture_fit_score,
            conn, citizen,
        )
    log.info("%s === done ===", pfx)

    output = []
    for match, pi in results:
        d = match.model_dump()
        d["pi"] = PIProfileResponse.model_validate(pi).model_dump()
        output.append(d)
    return output


# ---------------------------------------------------------------------------
# GET /api/match-progress/{student_id}  — live progress during matching
# ---------------------------------------------------------------------------

@router.get("/match-progress/{student_id}")
def match_progress(student_id: int, session: Session = Depends(get_session)):
    scored = session.exec(
        select(MatchResult).where(MatchResult.student_id == student_id)
    ).all()
    # Use the registered shortlist size so the bar reflects actual Claude work,
    # not the full PI database count.
    total = _shortlist_sizes.get(student_id) or len(session.exec(select(PIProfile)).all())
    return {"scored": len(scored), "total": total}


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

    # Build validated AvatarProfile (validates surveys, assigns pipeline_type)
    avatar_profile = build_avatar_profile(pi)

    # Generate system prompt based on pipeline type
    system_prompt = build_pi_avatar(avatar_profile)

    transcript: list = list(match.transcript or [])
    transcript.append({"role": "student", "content": request.message})

    # Convert to Claude message format (user = student, assistant = pi)
    messages = [
        {"role": "user" if t["role"] == "student" else "assistant", "content": t["content"]}
        for t in transcript
    ]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=system_prompt,
                messages=messages,
            )
            pi_response = resp.content[0].text
        except Exception as exc:
            error_text = str(exc) or repr(exc)
            print(f"[simulate_chat] Anthropic call failed: {error_text}")
            pi_response = (
                f"[LLM error] {error_text}\n\n"
                "[Mock response] No valid LLM output available. "
                "Using the system prompt as a local fallback:\n\n"
                f"{system_prompt[:800]}"
            )
    else:
        print("[simulate_chat] ANTHROPIC_API_KEY is not set. Using local mock response.")
        pi_response = (
            "[Mock response] No Anthropic API key configured. "
            "This is a local fallback for development.\n\n"
            f"{system_prompt[:800]}"
        )

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
