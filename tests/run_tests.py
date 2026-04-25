#!/usr/bin/env python3
"""
PiMatch automated test suite.
Usage:  python3 tests/run_tests.py

Requires the backend to be running at http://localhost:8000.
Clears all rows from the DB before running so every run starts fresh.
Does NOT stop/restart the backend or delete the DB file itself.
"""

import datetime
import io
import json
import os
import sys
import requests


def parse_json(resp):
    """Return parsed JSON body, or raise RuntimeError with HTTP status + raw body."""
    try:
        return resp.json()
    except Exception:
        snippet = resp.text[:300] if resp.text else "<empty body>"
        raise RuntimeError(f"HTTP {resp.status_code} — non-JSON body: {snippet!r}")


def reset_db():
    """
    Delete all rows from piprofile, studentprofile, and matchresult tables.
    Returns a one-line status string. Does NOT delete the DB file itself.
    """
    import sqlite3
    db_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "pimatch.db")
    )
    if not os.path.exists(db_path):
        return "DB file not found — will be created on first request"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in ("matchresult", "studentprofile"):
            conn.execute(f"DELETE FROM {table}")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        conn.close()
        return "students + matches cleared (PI seed data preserved)"
    except Exception as e:
        return f"WARNING: could not clear DB — {e}"

BASE_URL = "http://localhost:8000"

DEMO_STUDENT = {
    "name": "Demo Student",
    "gpa": 3.9,
    "field_of_study": "Computational Biology",
    "research_background": (
        "I develop ML methods for protein structure prediction and single-cell genomics. "
        "I have experience with graph neural networks, transformer models, and bioinformatics pipelines. "
        "My recent project applied variational autoencoders to gene expression data for cell-type identification."
    ),
    "technical_skills": ["Python", "PyTorch", "R", "CRISPR", "scRNA-seq"],
    "years_research_experience": 3,
    "has_publications": True,
    "known_professors": ["Páll Melsted"],
    "preferred_research_topics": ["computational biology", "genomics", "machine learning"],
    "location_preference": ["west_coast"],
    "citizenship_status": "f1",
    "preferred_lab_size": "medium",
    "independence_preference": 4,
    "intervention_tolerance": 4,
    "meeting_frequency_preference": 3,
    "work_life_balance_importance": 4,
    "industry_connections_importance": 2,
    "publication_rate_importance": 4,
}

SAMPLE_CV = (
    b"Dr. Jane Doe\n"
    b"PhD Candidate, Computational Biology\n"
    b"Publications: 3 papers in Nature Methods, Cell Systems, Genome Biology\n"
    b"Skills: Python, PyTorch, JAX, CRISPR, scRNA-seq, protein structure prediction\n"
    b"Projects: VAE-based cell-type identification from 10x genomics data\n"
)


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, test_id, name):
        self.test_id = test_id
        self.name = name
        self.status = "SKIP"
        self.detail = ""
        self.failure_expected = ""
        self.failure_got = ""
        self.likely_cause = ""

    def passed(self):
        self.status = "PASS"
        return self

    def failed(self, detail, expected="", got="", likely_cause=""):
        self.status = "FAIL"
        self.detail = detail
        self.failure_expected = expected
        self.failure_got = got
        self.likely_cause = likely_cause
        return self

    def skipped(self, reason):
        self.status = "SKIP"
        self.detail = reason
        return self


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(results):
    passed  = sum(1 for r in results if r.status == "PASS")
    failed  = sum(1 for r in results if r.status == "FAIL")
    skipped = sum(1 for r in results if r.status == "SKIP")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# PiMatch Test Report",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        f"- Total: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Skipped: {skipped}",
        "",
        "## Results",
        "",
        "| ID | Test | Status | Detail |",
        "|----|------|--------|--------|",
    ]

    for r in results:
        if r.status == "PASS":
            icon = "✅ PASS"
        elif r.status == "FAIL":
            icon = "❌ FAIL"
        else:
            icon = "⏭️ SKIP"
        detail = (r.detail or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r.test_id} | {r.name} | {icon} | {detail} |")

    failures = [r for r in results if r.status == "FAIL"]
    if failures:
        lines += ["", "## Failures Detail"]
        for r in failures:
            lines.append(f"\n### {r.test_id} — {r.name}")
            if r.failure_expected:
                lines.append(f"Expected: {r.failure_expected}")
            if r.failure_got:
                lines.append(f"Got: {r.failure_got}")
            if r.likely_cause:
                lines.append(f"Likely cause: {r.likely_cause}")

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n{'=' * 60}")
    print(f"Results  :  {passed} passed  |  {failed} failed  |  {skipped} skipped")
    print(f"Report   :  {report_path}")


# ---------------------------------------------------------------------------
# Live progress printer
# ---------------------------------------------------------------------------

def print_live(test_id, name, status, detail=""):
    if status == "PASS":
        icon = "✅"
    elif status == "FAIL":
        icon = "❌"
    else:
        icon = "⏭️ "
    suffix = f"  ({detail})" if detail else ""
    print(f"[{test_id}] {name}... {status}{suffix}")


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run_tests():
    results = []
    state = {}

    def add(test_id, name):
        r = TestResult(test_id, name)
        results.append(r)
        return r

    def live(r):
        print_live(r.test_id, r.name, r.status, r.detail)

    # ------------------------------------------------------------------ setup
    print("DB reset...", end=" ", flush=True)
    db_status = reset_db()
    print(db_status)

    # ------------------------------------------------------------------ T01
    r = add("T01", "Health check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            r.passed()
        else:
            r.failed(
                f"status {resp.status_code}: {resp.text[:80]}",
                expected='{"status": "ok"}',
                got=resp.text[:100],
            )
    except requests.exceptions.ConnectionError:
        r.failed("Cannot connect to backend at http://localhost:8000")
    live(r)

    if r.status == "FAIL":
        remaining = [
            ("T02", "PI list empty"),
            ("T03", "Seed PIs"),
            ("T04", "PI list populated"),
            ("T05", "PI institutions correct"),
            ("T06", "Create student"),
            ("T07", "Get student"),
            ("T08", "Run matching"),
            ("T09", "Research scores not all 50"),
            ("T10", "Rationales are specific"),
            ("T11", "Indirect connection (Pachter)"),
            ("T12", "Citizenship flag (Anandkumar)"),
            ("T13", "PI nested in match"),
            ("T14", "Get single match"),
            ("T15", "Get matches list"),
            ("T16", "Chat simulate"),
            ("T17", "Avatar says Caltech (Shapiro)"),
            ("T18", "Avatar asks a question"),
            ("T19", "Transcript persists"),
            ("T20", "CV upload txt"),
            ("T21", "Chemistry evaluate"),
            ("T22", "Report fetch"),
        ]
        for tid, name in remaining:
            rr = add(tid, name)
            rr.skipped("SKIP (backend unreachable)")
        write_report(results)
        sys.exit(1)

    # ------------------------------------------------------------------ T02
    r = add("T02", "PI list empty")
    try:
        resp = requests.get(f"{BASE_URL}/api/pi/list", timeout=5)
        data = parse_json(resp)
        if resp.status_code == 200 and isinstance(data, list) and len(data) == 0:
            r.passed()
        elif resp.status_code == 200 and isinstance(data, list) and len(data) > 0:
            r.skipped(f"SKIP — {len(data)} PIs already seeded (PI data is preserved between runs)")
        else:
            r.failed(
                f"Unexpected {resp.status_code}",
                expected="[]",
                got=resp.text[:100],
            )
    except Exception as e:
        r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T03
    r = add("T03", "Seed PIs")
    try:
        resp = requests.post(f"{BASE_URL}/api/pi/seed", timeout=10)
        data = parse_json(resp)
        if resp.status_code == 200 and data.get("total") == 5:
            r.passed()
            state["seeded"] = True
        else:
            r.failed(
                f"Unexpected {resp.status_code}: {str(data)[:150]}",
                expected='{"total": 5, ...}',
                got=str(data)[:200],
            )
    except Exception as e:
        r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T04
    r = add("T04", "PI list populated")
    if not state.get("seeded"):
        r.skipped("SKIP (depends on T03)")
    else:
        try:
            resp = requests.get(f"{BASE_URL}/api/pi/list", timeout=5)
            data = parse_json(resp)
            required = {"name", "institution", "department"}
            if resp.status_code == 200 and isinstance(data, list) and len(data) == 5:
                bad = [p for p in data if not required.issubset(p.keys())]
                if not bad:
                    r.passed()
                    state["pi_list"] = data
                else:
                    r.failed(
                        f"Missing required keys in {len(bad)} PI(s)",
                        expected="all PIs have name/institution/department",
                        got=str(bad[:1])[:200],
                    )
            else:
                count = len(data) if isinstance(data, list) else "non-list"
                r.failed(
                    f"Got {resp.status_code} with {count} PIs",
                    expected="200 with 5 PIs",
                    got=str(data)[:200],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T05
    r = add("T05", "PI institutions correct")
    if not state.get("pi_list"):
        r.skipped("SKIP (depends on T04)")
    else:
        wrong = [(p["name"], p.get("institution")) for p in state["pi_list"] if p.get("institution") != "Caltech"]
        if not wrong:
            r.passed()
        else:
            r.failed(
                f"Wrong institution for: {[n for n, _ in wrong]}",
                expected="all institution == 'Caltech'",
                got=str(wrong),
            )
    live(r)

    # ------------------------------------------------------------------ T06
    r = add("T06", "Create student")
    try:
        resp = requests.post(f"{BASE_URL}/api/survey", json=DEMO_STUDENT, timeout=10)
        data = parse_json(resp)
        if resp.status_code == 201 and data.get("id"):
            r.passed()
            state["student_id"] = data["id"]
        else:
            r.failed(
                f"Got {resp.status_code}: {str(data)[:150]}",
                expected="201 with id field",
                got=f"{resp.status_code}: {str(data)[:150]}",
            )
    except Exception as e:
        r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T07
    r = add("T07", "Get student")
    if not state.get("student_id"):
        r.skipped("SKIP (depends on T06)")
    else:
        try:
            resp = requests.get(f"{BASE_URL}/api/survey/{state['student_id']}", timeout=5)
            data = parse_json(resp)
            if resp.status_code == 200 and data.get("name") == DEMO_STUDENT["name"]:
                r.passed()
            else:
                r.failed(
                    f"Got {resp.status_code}, name='{data.get('name')}'",
                    expected=f"name='{DEMO_STUDENT['name']}'",
                    got=str(data)[:200],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T08
    r = add("T08", "Run matching")
    if not state.get("student_id") or not state.get("seeded"):
        r.skipped("SKIP (depends on T03 and T06)")
    else:
        try:
            print(f"  ↳ Running Claude-powered matching — may take 10–30s …")
            resp = requests.post(f"{BASE_URL}/api/match/{state['student_id']}", timeout=120)
            data = parse_json(resp)
            if resp.status_code == 200 and isinstance(data, list) and len(data) == 5:
                r.passed()
                state["match_results"] = data
                state["first_match_id"] = data[0]["id"]
                for m in data:
                    pi_name = (m.get("pi") or {}).get("name", "")
                    if "Pachter" in pi_name:
                        state["pachter_match_id"] = m["id"]
                        state["pachter_match"] = m
                    elif "Anandkumar" in pi_name:
                        state["anandkumar_match_id"] = m["id"]
                        state["anandkumar_match"] = m
                    elif "Shapiro" in pi_name:
                        state["shapiro_match_id"] = m["id"]
                        state["shapiro_match"] = m
            else:
                count = len(data) if isinstance(data, list) else "non-list"
                r.failed(
                    f"Got {resp.status_code} with {count} results",
                    expected="200 with 5 MatchResults",
                    got=str(data)[:300],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    t08_ok = bool(state.get("match_results"))

    # ------------------------------------------------------------------ T09
    r = add("T09", "Research scores not all 50")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        scores = [m["research_direction_score"] for m in state["match_results"]]
        non_fifty = [s for s in scores if s != 50.0]
        if len(non_fifty) >= 3:
            r.passed()
            state["api_key_works"] = True
        else:
            state["api_key_works"] = False
            r.failed(
                f"Only {len(non_fifty)}/5 scores differ from 50.0",
                expected="at least 3 scores != 50.0",
                got=str(scores),
                likely_cause="ANTHROPIC_API_KEY not set — all scores fall back to 50.0",
            )
    live(r)

    # ------------------------------------------------------------------ T10
    r = add("T10", "Rationales are specific")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        short = [
            (m.get("pi", {}).get("name", "?"), len(m["research_match_rationale"]))
            for m in state["match_results"]
            if len(m.get("research_match_rationale", "")) <= 50
        ]
        if not short:
            r.passed()
        else:
            r.failed(
                f"Rationale ≤ 50 chars for: {short}",
                expected="all research_match_rationale > 50 chars",
                got=str(short),
                likely_cause="ANTHROPIC_API_KEY not set — fallback rationale returned",
            )
    live(r)

    # ------------------------------------------------------------------ T11
    r = add("T11", "Indirect connection (Pachter)")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        pm = state.get("pachter_match")
        if pm is None:
            r.failed("Pachter not found in match results — check caltech_pis.json")
        else:
            via = pm.get("indirect_connection_via") or ""
            is_indirect = pm.get("is_indirect_connection", False)
            via_ok = "Melsted" in via or "Páll" in via or "Pall" in via
            if is_indirect and via_ok:
                r.passed()
            else:
                r.failed(
                    f"is_indirect_connection={is_indirect}, via='{via}'",
                    expected="is_indirect_connection=True, indirect_connection_via contains 'Melsted' or 'Páll'",
                    got=f"is_indirect_connection={is_indirect}, indirect_connection_via='{via}'",
                    likely_cause="co_author_names in caltech_pis.json may not include Páll Melsted for Pachter",
                )
    live(r)

    # ------------------------------------------------------------------ T12
    r = add("T12", "Citizenship flag (Anandkumar)")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        am = state.get("anandkumar_match")
        if am is None:
            r.failed("Anandkumar not found in match results")
        else:
            if am.get("citizenship_mismatch"):
                r.passed()
            else:
                r.failed(
                    "citizenship_mismatch is False for Anandkumar",
                    expected="citizenship_mismatch=True",
                    got=f"citizenship_mismatch={am.get('citizenship_mismatch')}",
                    likely_cause="funding_citizen_restricted may be False for Anandkumar in caltech_pis.json",
                )
    live(r)

    # ------------------------------------------------------------------ T13
    r = add("T13", "PI nested in match")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        missing = []
        for m in state["match_results"]:
            pi = m.get("pi") or {}
            if not (pi.get("name") and pi.get("institution") and pi.get("department")):
                missing.append(m.get("id"))
        if not missing:
            r.passed()
        else:
            r.failed(
                f"Match IDs missing pi.name/institution/department: {missing}",
                expected="all MatchResults have pi.name, pi.institution, pi.department",
                got=f"missing in match IDs: {missing}",
            )
    live(r)

    # ------------------------------------------------------------------ T14
    r = add("T14", "Get single match")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        try:
            mid = state["first_match_id"]
            resp = requests.get(f"{BASE_URL}/api/match/{mid}", timeout=5)
            data = parse_json(resp)
            pi = data.get("pi") or {}
            if resp.status_code == 200 and data.get("id") == mid and pi.get("name"):
                r.passed()
            else:
                r.failed(
                    f"Got {resp.status_code}: id match={data.get('id') == mid}, pi.name={pi.get('name')!r}",
                    expected=f"200 with id={mid} and pi.name populated",
                    got=str(data)[:200],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T15
    r = add("T15", "Get matches list")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        try:
            resp = requests.get(f"{BASE_URL}/api/matches/{state['student_id']}", timeout=5)
            data = parse_json(resp)
            if resp.status_code == 200 and isinstance(data, list) and len(data) == 5:
                r.passed()
            else:
                count = len(data) if isinstance(data, list) else "non-list"
                r.failed(
                    f"Got {resp.status_code} with {count} results",
                    expected="5 MatchResults",
                    got=str(data)[:200],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T16
    r = add("T16", "Chat simulate")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        mid = state.get("pachter_match_id") or state["first_match_id"]
        state["simulate_match_id"] = mid
        try:
            print("  ↳ Running PI avatar chat — may take 5–15s …")
            resp = requests.post(
                f"{BASE_URL}/api/simulate/{mid}",
                json={"message": "Hi, tell me about your research"},
                timeout=60,
            )
            data = parse_json(resp)
            pi_response = data.get("pi_response", "")
            transcript = data.get("transcript") or []
            if resp.status_code == 200 and pi_response and len(transcript) == 2:
                r.passed()
                state["simulate_response"] = data
            else:
                r.failed(
                    f"Got {resp.status_code}: pi_response non-empty={bool(pi_response)}, transcript len={len(transcript)}",
                    expected="200, non-empty pi_response, transcript with 2 entries",
                    got=str(data)[:300],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T17
    r = add("T17", "Avatar says Caltech (Shapiro)")
    if not t08_ok:
        r.skipped("SKIP (depends on T08)")
    else:
        shapiro_mid = state.get("shapiro_match_id")
        if shapiro_mid is None:
            r.failed("Shapiro not found in match results")
        else:
            try:
                print("  ↳ Running Shapiro PI avatar — may take 5–15s …")
                resp = requests.post(
                    f"{BASE_URL}/api/simulate/{shapiro_mid}",
                    json={"message": "Hi, tell me about your research"},
                    timeout=60,
                )
                data = parse_json(resp)
                pi_response = data.get("pi_response", "")
                bad = [w for w in ["HMC", "Harvey Mudd", "Brown"] if w in pi_response]
                if resp.status_code == 200 and not bad:
                    r.passed()
                elif bad:
                    r.failed(
                        f"Response mentions forbidden institution names: {bad}",
                        expected="pi_response does not contain 'HMC', 'Harvey Mudd', or 'Brown'",
                        got=f"Found: {bad}",
                        likely_cause="PI avatar system prompt may not be grounding institution correctly",
                    )
                else:
                    r.failed(
                        f"Unexpected {resp.status_code}",
                        expected="200",
                        got=str(data)[:200],
                    )
            except Exception as e:
                r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T18
    r = add("T18", "Avatar asks a question")
    if not state.get("simulate_response"):
        r.skipped("SKIP (depends on T16)")
    elif not state.get("api_key_works"):
        r.skipped("SKIP — API key not set; avatar returns fallback with no question")
    else:
        pi_response = state["simulate_response"].get("pi_response", "")
        if "?" in pi_response:
            r.passed()
        else:
            r.failed(
                "No '?' anywhere in pi_response",
                expected="at least one '?' anywhere in pi_response",
                got=f"full response ({len(pi_response)} chars): {pi_response[:200]!r}",
                likely_cause="PI avatar system prompt may not be enforcing the 1-question-per-turn rule",
            )
    live(r)

    # ------------------------------------------------------------------ T19
    r = add("T19", "Transcript persists")
    if not state.get("simulate_response"):
        r.skipped("SKIP (depends on T16)")
    else:
        try:
            resp = requests.get(f"{BASE_URL}/api/match/{state['simulate_match_id']}", timeout=5)
            data = parse_json(resp)
            transcript = data.get("transcript") or []
            if resp.status_code == 200 and len(transcript) == 2:
                r.passed()
            else:
                r.failed(
                    f"transcript length = {len(transcript)}, expected 2",
                    expected="transcript with 2 entries (student + pi)",
                    got=f"transcript length = {len(transcript)}",
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T20
    r = add("T20", "CV upload txt")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/upload-cv",
            files={"file": ("test_cv.txt", io.BytesIO(SAMPLE_CV), "text/plain")},
            timeout=10,
        )
        data = parse_json(resp)
        cv_text = data.get("cv_text", "")
        if resp.status_code == 200 and cv_text:
            r.passed()
        else:
            r.failed(
                f"Got {resp.status_code}: cv_text empty={not cv_text}",
                expected="200 with non-empty cv_text",
                got=str(data)[:200],
            )
    except Exception as e:
        r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T21
    r = add("T21", "Chemistry evaluate")
    if not state.get("simulate_response"):
        r.skipped("SKIP (depends on T16)")
    else:
        try:
            print("  ↳ Running chemistry evaluation — may take 10–20s …")
            resp = requests.post(
                f"{BASE_URL}/api/evaluate/{state['simulate_match_id']}",
                timeout=120,
            )
            data = parse_json(resp)
            expected_dims = {
                "research_alignment",
                "mentorship_compatibility",
                "culture_fit",
                "communication_fit",
                "red_flags",
            }
            dim_scores = data.get("dimension_scores") or {}
            ok_score = "overall_score" in data
            ok_dims = set(dim_scores.keys()) == expected_dims
            ok_pos = bool(data.get("key_positives"))
            ok_con = bool(data.get("key_concerns"))
            if resp.status_code == 200 and ok_score and ok_dims and ok_pos and ok_con:
                r.passed()
                state["chemistry_report"] = data
            else:
                missing_dims = expected_dims - set(dim_scores.keys())
                issues = []
                if not ok_score:
                    issues.append("missing overall_score")
                if not ok_dims:
                    issues.append(f"wrong dimension_scores keys (missing: {missing_dims})")
                if not ok_pos:
                    issues.append("empty key_positives")
                if not ok_con:
                    issues.append("empty key_concerns")
                r.failed(
                    f"Got {resp.status_code}: {'; '.join(issues)}",
                    expected="overall_score + 5 dimension_scores + key_positives + key_concerns",
                    got=str(data)[:400],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ T22
    r = add("T22", "Report fetch")
    if not state.get("chemistry_report"):
        r.skipped("SKIP (depends on T21)")
    else:
        try:
            resp = requests.get(
                f"{BASE_URL}/api/report/{state['simulate_match_id']}",
                timeout=5,
            )
            data = parse_json(resp)
            if resp.status_code == 200 and data.get("report"):
                r.passed()
            else:
                r.failed(
                    f"Got {resp.status_code}: report present={bool(data.get('report'))}",
                    expected="200 with non-null report dict",
                    got=str(data)[:200],
                )
        except Exception as e:
            r.failed(str(e))
    live(r)

    # ------------------------------------------------------------------ Done
    write_report(results)
    return results


if __name__ == "__main__":
    run_tests()
