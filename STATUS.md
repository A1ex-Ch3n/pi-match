# PiMatch — Build Status

Last updated: 2026-04-25

---

## Backend (T1)

**Status: Complete — server boots, all endpoints registered and responding.**

Run with: `cd backend && uvicorn main:app --reload --port 8000`

### Files created

| File | Purpose | Status |
|---|---|---|
| `main.py` | FastAPI app entry point; registers CORS for `localhost:5173`, mounts all three routers under `/api`, creates DB tables on startup, adds project root to `sys.path` so `agents/` is importable. | Complete |
| `database.py` | SQLite engine (`pimatch.db`), `create_db_and_tables()`, and `get_session()` dependency. | Complete |
| `models.py` | SQLModel table definitions for `StudentProfile`, `PIProfile`, and `MatchResult`; list/dict fields use `sa_column=Column(JSON)` for SQLite compatibility. | Complete |
| `schemas.py` | Pydantic request/response schemas: `StudentProfileCreate`, `PIProfileResponse` (omits `student_survey_responses` per rule #4), `PIProfileSeedItem`, `MatchResultResponse`, `ChatRequest/Response`, `ChemistryReportSchema`. | Complete |
| `scoring.py` | Deterministic scoring helpers: mentorship style, funding stability, technical skills, culture fit, reply likelihood, location filter, citizenship flag, direct/indirect connection detection, and `overall_score()` weighted combinator. | Complete |
| `routers/survey.py` | `POST /api/survey` (create student profile), `GET /api/survey/{id}`. | Complete |
| `routers/pi.py` | `GET /api/pi/list`, `GET /api/pi/{id}`, `POST /api/pi/seed` (loads from `data/seeds/caltech_pis.json` by default). | Complete |
| `routers/simulation.py` | `POST /api/match/{student_id}` (v1.0 full matching pipeline), `GET /api/matches/{student_id}`, `POST /api/simulate/{match_id}` (v2.0 PI avatar chat), `POST /api/evaluate/{match_id}` (v2.5 chemistry report), `GET /api/report/{match_id}`. Delegates Claude calls to existing `agents/` modules. | Complete |

### Verified working
- `uvicorn main:app --reload --port 8000` starts with no errors
- `GET /health` → `{"status": "ok"}`
- `GET /api/pi/list` → `[]`
- `POST /api/survey` → 201 with full `StudentProfile` JSON

### Known issues / what still needs doing
- **`data/seeds/caltech_pis.json` does not exist yet** — `POST /api/pi/seed` will 404 until seed data is created (next task).
- **`data/seeds/demo_student.json` does not exist yet** — demo student needs to be seeded manually or via a future endpoint.
- **No `.env` loading** — `ANTHROPIC_API_KEY` must be set in the shell before starting uvicorn; `/api/match` will return neutral scores (50.0) without it.
- **`agents/conversation.py` not yet implemented** — referenced in CLAUDE.md but not used by any current endpoint; v2.0 chat uses inline Claude calls in `simulation.py` instead.
- The `POST /api/pi/seed` endpoint treats any JSON array at the given path as valid input — no schema validation beyond `PIProfileSeedItem`; malformed seed data will raise a 500.

---

## Agents (T2)

**Status: Complete — all three required agent functions implemented and parse cleanly.**

### Files created

| File | Purpose | Status |
|---|---|---|
| `agents/__init__.py` | Empty package marker so `agents` is importable as a Python package. | Complete |
| `agents/research_match.py` | `score_research_fit(student_background, pi_abstracts, pi_research_areas) → (float, str)` — calls Claude to semantically compare the student's background against PI abstracts, returning a 0–100 score and a 2–3 sentence rationale citing specific paper topics. | Complete |
| `agents/pi_avatar.py` | `build_pi_avatar(pi_profile) → str` — assembles a system prompt for the PI avatar from research areas, recent abstracts, NSF grants, lab size, PI survey (Stream A), and anonymous student responses (Stream B); embeds behavioral rules (first-person, ask exactly one question per turn, never fabricate). | Complete |
| `agents/evaluator.py` | `evaluate_chemistry(transcript, student_profile, pi_profile, v1_match_result) → ChemistryReport` — fresh Claude call (no avatar context) that scores 5 dimensions, extracts key positives/concerns/follow-up questions, and drafts a PI introduction email; returns a `ChemistryReport` Pydantic model with fallback to neutral 50s on parse failure. | Complete |
| `agents/conversation.py` | **Not yet created** — listed in CLAUDE.md but not used by any current endpoint; v2.0 chat is handled inline in `routers/simulation.py`. |

### Known issues / what still needs doing
- **`ANTHROPIC_API_KEY` must be set in the shell** — all three agent functions fall back to neutral values (score 50, empty rationale) when the key is absent or invalid rather than crashing.
- **`agents/conversation.py` is not implemented** — not currently called by any endpoint; safe to skip for MVP.
- **`pi_avatar.py` uses `TYPE_CHECKING` import** for `PIProfile` to avoid a circular import with `backend/models.py`; this works at runtime but means type checkers won't resolve the type without the backend on `sys.path`.
- **No live API test yet** — `python agents/research_match.py` confirms the code runs end-to-end once `ANTHROPIC_API_KEY` is exported.

---

## Frontend (T4)

**Status: Complete — all pages and components built, TypeScript clean, `npm run build` passes.**

Run with: `cd frontend && npm run dev` → http://localhost:5173

### Files created

| File | Purpose | Status |
|---|---|---|
| `src/types.ts` | TypeScript interfaces mirroring all backend schemas: `StudentProfile`, `PIProfile`, `MatchResult`, `ChemistryReport`, `TranscriptMessage`, `NSFGrant`. Frontend types are the single source of truth for all API shapes. | Complete |
| `src/api/client.ts` | Axios client (base URL `http://localhost:8000/api`) with typed wrappers for all 8 endpoints: `submitSurvey`, `listPIs`, `seedPIs`, `runMatch`, `getMatches`, `simulate`, `evaluate`, `getReport`. | Complete |
| `src/App.tsx` | `BrowserRouter` with 4 routes: `/` → `SurveyPage`, `/matches/:studentId` → `MatchPage`, `/chat/:matchId` → `ChatPage`, `/report/:matchId` → `ReportPage`. | Complete |
| `src/index.css` | Single `@import "tailwindcss"` for Tailwind v4 (no config file needed). | Complete |
| `src/pages/SurveyPage.tsx` | Full intake form covering every `StudentProfile` field — text/number inputs, selects for location/citizenship/lab size, comma-separated list inputs for skills/professors/topics, 6 range sliders (1–5) for all mentorship style dimensions. On submit: calls `POST /survey`, then `POST /match/:id`, then navigates to `/matches/:id`. | Complete |
| `src/pages/MatchPage.tsx` | Fetches `GET /matches/:studentId` on mount; sorts direct connections to top, then by `overall_score` descending; renders a `PICard` per result; includes "Rerun Matching" button that calls `POST /match/:id`. Shows loading spinner and empty states. | Complete |
| `src/pages/ChatPage.tsx` | Chat UI showing PI and student bubbles; each sent message calls `POST /simulate/:matchId` and replaces the transcript with the returned state; typing indicator shown while awaiting response; "Get Chemistry Report" button calls `POST /evaluate/:matchId` then navigates to `/report/:matchId`. | Complete |
| `src/pages/ReportPage.tsx` | Loads `GET /report/:matchId`; displays overall chemistry score, `ScoreRadar` chart, per-dimension score bars with rationale text, key positives (green) and concerns (amber) panels, recommended follow-up questions, and a copy-to-clipboard intro email draft. | Complete |
| `src/components/PICard.tsx` | Match card showing PI name, institution/department, overall score (large), 5 dimension score bars with weight labels, all flag badges, reply likelihood badge, research rationale text, and links to chat and report pages. | Complete |
| `src/components/ScoreRadar.tsx` | Recharts `RadarChart` wrapper; exports `matchRadarDimensions()` for v1.0 scores and `chemistryRadarDimensions()` for v2.5 `ChemistryReport` scores. | Complete |
| `src/components/ChatBubble.tsx` | Message bubble: PI messages left-aligned in gray, student messages right-aligned in violet. | Complete |
| `src/components/FlagBadge.tsx` | Color-coded pill badges: 🤝 Direct Connection (emerald), 🔗 Indirect Connection (blue, shows `via` name), 🇺🇸 Citizenship Required (amber), 💰 Active Funding (violet). | Complete |

### Verified working
- `npx tsc --noEmit` → 0 errors
- `npm run build` → clean production bundle (614 kB JS, 21 kB CSS)
- Routing wired: all 4 routes resolve without 404
- Tailwind v4 compiles via `@tailwindcss/vite` plugin

### Known issues / what still needs doing
- **Backend must return nested `pi` object in `MatchResult`** — `MatchPage` and `PICard` read `match.pi.name`, `match.pi.department`, etc. If the backend returns only `pi_id`, both will crash. Confirm `routers/simulation.py` populates `pi` on match response.
- **ChatPage PI header is blank on first load** — no `GET /api/match/:id` endpoint exists; the PI name in the chat header defaults to "PI Avatar" until the first `/simulate` response returns an updated `MatchResult` with `pi` embedded.
- **No top-level error boundary** — an unhandled runtime error in any component will blank the page; a `<ErrorBoundary>` wrapper in `App.tsx` would improve demo robustness.
- **`App.css` and `src/assets/`** are Vite scaffold leftovers not imported anywhere; safe to delete before demo if desired.
- **Chunk size warning** — recharts produces a ~615 kB bundle; acceptable for a hackathon, not a production concern.

---

## Data (T3)

**Status: Complete — all seed data live in DB, full match pipeline verified end-to-end.**

### Files created

| File | Purpose | Status |
|---|---|---|
| `data/scraper.py` | `fetch_semantic_scholar(pi_name, institution) → dict` — searches Semantic Scholar by name, fetches recent papers (2023+) with abstracts, extracts co-author IDs from paper author lists, and caches everything to `data/cache/{authorId}.json` and `data/cache/search_{slug}.json`; also exposes `resolve_author_name(id)` for co-author name lookup. | Complete |
| `data/nsf.py` | `fetch_nsf_grants(pi_name) → list[dict]` — queries the NSF Awards API by PI last name for grants expiring after 2024, normalises amounts, and caches to `data/cache/nsf_{lastname}.json`; `citizen_only` defaults to `false` and must be set manually in seed JSON (NSF API does not expose citizenship restrictions). | Complete |
| `data/seeds/caltech_pis.json` | Hand-crafted seed profiles for 5 real Caltech PIs (Pachter, Anandkumar, Shapiro, Van Valen, Yue) using real paper abstracts from Semantic Scholar, plausible NSF grant data, `pi_survey` with both human-readable text and numeric slider fields (`autonomy_style`, `meeting_frequency_num`, `intervention_level`, `work_life_balance`), and 2 anonymous `student_survey_responses` each. | Complete |
| `data/seeds/demo_student.json` | Golden demo student (F1 visa, Computational Biology, west-coast preference, knows "Páll Melsted") pre-wired to trigger an indirect connection through Pachter and a citizenship flag on Anandkumar. | Complete |
| `data/cache/` | Empty directory; all Semantic Scholar and NSF API responses are written here at runtime to avoid re-fetching during the demo. | Exists (empty until scraper is run) |

### Verified working
- `POST /api/pi/seed` loads all 5 PIs from `caltech_pis.json` into a fresh SQLite DB.
- `POST /api/match/1` (demo student) returns 5 ranked matches: Pachter #1 with `INDIRECT: Páll Melsted`; Anandkumar carries `citizenship_mismatch: true`.
- All 5 research rationales cite specific paper titles and methods, confirming real abstracts reach Claude.
- Mentorship, culture-fit, and funding scores compute cleanly after adding numeric slider fields to each `pi_survey`.
- Also fixed `backend/scoring.py` to use a `_safe_int()` helper so text values in `pi_survey` no longer crash the scorer.

### Known issues / what still needs doing
- **`data/processor.py` not implemented** — listed in CLAUDE.md but not required for the demo; the seed JSON + scraper cover everything the backend needs.
- **`citizen_only` on grants is manually set** — the NSF API does not expose citizenship restrictions; the flag is hardcoded to `true` on Anandkumar's DOE grant in the seed JSON. Any live-fetched grant data will default to `false` and must be reviewed manually.
- **Indirect connection requires exact name match** — `co_author_names` in the seed JSON must match exactly what the student types in `known_professors`; the backend has no fuzzy matching. The demo is pre-wired to "Páll Melsted" on both sides.
- **`data/cache/` is empty** — if the scraper is called during the demo against live Semantic Scholar, the unauthenticated rate limit (100 req / 5 min) may cause delays; pre-running `python data/scraper.py` for each PI before presenting is recommended.
- **Scraper not wired to `POST /api/pi/seed`** — the seed endpoint reads the JSON file directly and does not call `scraper.py` or `nsf.py`; those are standalone utilities for future data refresh.
