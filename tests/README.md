# PiMatch Test Suite — Quick Reference

## How to run a clean test (do this every time)

**Step 1 — Stop uvicorn** (Ctrl+C in the terminal where it is running).

**Step 2 — Start uvicorn with the API key in the same terminal:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cd /path/to/hacktech_26/backend
uvicorn main:app --reload --port 8000
```

**Step 3 — In a separate terminal, from the project root:**
```bash
cd /path/to/hacktech_26
python3 tests/run_tests.py
```

The script automatically clears all rows from the database before running,
so you get a reproducible clean run every time. The DB file itself is not deleted.

---

## Expected output (API key set correctly)

```
DB reset... all rows cleared
[T01] Health check... PASS
[T02] PI list empty... PASS
[T03] Seed PIs... PASS
[T04] PI list populated... PASS
[T05] PI institutions correct... PASS
[T06] Create student... PASS
[T07] Get student... PASS
  ↳ Running Claude-powered matching — may take 10–30s …
[T08] Run matching... PASS
[T09] Research scores not all 50... PASS
[T10] Rationales are specific... PASS
[T11] Indirect connection (Pachter)... PASS
[T12] Citizenship flag (Anandkumar)... PASS
[T13] PI nested in match... PASS
[T14] Get single match... PASS
[T15] Get matches list... PASS
  ↳ Running PI avatar chat — may take 5–15s …
[T16] Chat simulate... PASS
  ↳ Running Shapiro PI avatar — may take 5–15s …
[T17] Avatar says Caltech (Shapiro)... PASS
[T18] Avatar asks a question... PASS
[T19] Transcript persists... PASS
[T20] CV upload txt... PASS
  ↳ Running chemistry evaluation — may take 10–20s …
[T21] Chemistry evaluate... PASS
[T22] Report fetch... PASS

============================================================
Results  :  22 passed  |  0 failed  |  0 skipped
```

Total runtime: ~2–3 minutes (most time is Claude API calls).

---

## If T09 still fails after setting the key

The API key must be exported in the **same terminal session** that starts uvicorn —
not in the terminal where you run the tests. If you set the key after uvicorn was
already running, stop uvicorn and restart it (Step 1 → Step 2 above).

Quick check: if T09 fails with "Only 0/5 scores differ from 50.0", the key is missing
from uvicorn's environment. If it fails with a different message, check the
Failures Detail section in `tests/report.md`.

---

## Failure guide

| Test | Failure message | Cause | Fix |
|------|----------------|-------|-----|
| T01 | Cannot connect | Backend not running | Run Step 2 above |
| T02 | Expected empty list after DB reset | DB reset failed | Check for a lock on `pimatch.db` |
| T03 | Seed file not found | Wrong working directory | Start uvicorn from `backend/` |
| T08 | non-JSON body / 500 | Server crash | Check uvicorn terminal for traceback |
| T09 | Only 0/5 scores differ from 50.0 | API key not in uvicorn's env | Stop and restart uvicorn with key exported (Step 1 → 2) |
| T11 | is_indirect_connection=False | Seed data issue | Check `co_author_names` for Páll Melsted in `caltech_pis.json` |
| T12 | citizenship_mismatch=False | Seed data issue | Check `funding_citizen_restricted: true` for Anandkumar |
| T18 | No '?' anywhere in pi_response | Avatar not asking a question | Verify API key (T09 must pass first); check avatar system prompt |
| T21 | Wrong dimension keys | Evaluator fallback triggered | Same as T09 — API key issue |

---

## Report

`tests/report.md` is overwritten on every run. The **Failures Detail** section
shows expected vs. actual values and a likely cause for each failure.
