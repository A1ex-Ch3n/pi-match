# PiMatch — Developer Testing Manual

> **Hacktech 2026** | Last updated: 2026-04-25
> Use this doc to verify every feature works end-to-end before the demo.

---

## Quick Start Checklist

- [ ] `ANTHROPIC_API_KEY` exported in shell
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] PIs seeded (5 Caltech PIs)
- [ ] Demo student created

---

## 1. Environment Setup

### 1.1 Set API Key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

> [!warning]
> Without this, all AI scores default to 50.0 and research rationales will be blank. Set it before starting the server.

### 1.2 Start Backend

```bash
cd /path/to/hacktech_26/backend
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 1.3 Start Frontend

```bash
cd /path/to/hacktech_26/frontend
npm run dev
```

Open: `http://localhost:5173`

### 1.4 Fresh Database (after schema changes)

> [!caution]
> Required if you changed `models.py` (e.g., the location_preference update). Delete the old DB first.

```bash
rm backend/pimatch.db
# Restart uvicorn — it recreates tables on startup
```

---

## 2. Seeding Test Data

### 2.1 Seed the 5 Caltech PIs

```bash
curl -X POST http://localhost:8000/api/pi/seed
```

**Expected:** `{"seeded": 5}` (or similar)

Verify PIs loaded:
```bash
curl http://localhost:8000/api/pi/list | python3 -m json.tool | grep '"name"'
```

Should see: Lior Pachter, Anima Anandkumar, Mikhail Shapiro, David Van Valen, Yisong Yue

### 2.2 Create the Demo Student via API

```bash
curl -X POST http://localhost:8000/api/survey \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Student",
    "gpa": 3.9,
    "field_of_study": "Computational Biology",
    "research_background": "I develop ML methods for protein structure prediction and single-cell genomics. I have experience with graph neural networks, transformer models, and bioinformatics pipelines. My recent project applied variational autoencoders to gene expression data for cell-type identification.",
    "technical_skills": ["Python", "PyTorch", "R", "CRISPR", "scRNA-seq"],
    "years_research_experience": 3,
    "has_publications": true,
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
    "publication_rate_importance": 4
  }'
```

Note the returned `id` — you'll use it as `{student_id}` below.

---

## 3. v1.0 — Matching Pipeline Tests

### 3.1 Run Matching

```bash
curl -X POST http://localhost:8000/api/match/{student_id}
```

**Expected:** JSON array of 5 `MatchResult` objects, sorted by `overall_score` descending.

#### What to verify

| Check | Expected |
|---|---|
| 5 results returned | All 5 Caltech PIs (no location filter for west coast PIs in CA) |
| `research_direction_score` | Non-zero, varies per PI (not all 50.0) |
| `research_match_rationale` | 2–3 specific sentences mentioning paper topics |
| Pachter result | `is_indirect_connection: true`, `indirect_connection_via: "Páll Melsted"` |
| Anandkumar result | `citizenship_mismatch: true` |
| `overall_score` order | Pachter likely #1 or near top (indirect connection +10 pts) |
| `pi` object nested | Each result has `pi.name`, `pi.institution`, `pi.department` |

### 3.2 Retrieve Stored Matches

```bash
curl http://localhost:8000/api/matches/{student_id}
```

Same results as above, fetched from DB.

### 3.3 Retrieve Single Match

```bash
curl http://localhost:8000/api/match/{match_id}
```

Should return one `MatchResult` with `pi` nested. Used by ChatPage on load.

---

## 4. Frontend Flow Tests

### 4.1 Survey Form (`/`)

1. Open `http://localhost:5173`
2. Fill out the form:
   - Name: `Test User`
   - Research Background: describe some research
   - Known Professors: `Páll Melsted`
   - Location: select **West Coast** (checkbox, not dropdown now)
   - Citizenship: `F-1 Visa`
3. Click **Find My PI Matches →**
4. Should navigate to `/matches/{id}` after ~5–15 seconds (Claude API call)

> [!tip]
> If navigation hangs, check the backend terminal for errors. Most common cause: `ANTHROPIC_API_KEY` not set.

#### CV Upload Test

1. Prepare a plain `.txt` file with some CV text
2. Click **📎 Upload CV** on the form
3. The cv_text textarea should auto-fill with the extracted text
4. Submit as normal — the extracted text augments research matching

### 4.2 Match Page (`/matches/{student_id}`)

- Cards should appear ranked by score (direct connections pinned top)
- Each card shows: PI name, department, institution, overall score, flag badges
- Click any **score bar** → accordion expands showing rationale text
- Research bar shows Claude's actual reasoning
- Mentorship/Funding/Culture/Skills show computed explanations

#### Flag badge checks

| Badge | Trigger condition |
|---|---|
| 🤝 Direct Connection | PI name in `known_professors` |
| 🔗 Indirect Connection | Co-author of known professor |
| 🇺🇸 Citizenship Required | PI grant has `citizen_only: true` AND student is f1/j1/other |
| 💰 Active Funding | `has_active_nsf_grant: true` |

### 4.3 Location Multi-select Test

1. On Survey form, select **West Coast** AND **East Coast** checkboxes
2. Submit → only PIs in CA/OR/WA/NY/MA/MD/etc. should appear
3. Select **No preference** → all PIs appear
4. Selecting "No preference" should deselect all other options

### 4.4 Chat Page (`/chat/{match_id}`)

1. From match page, click **Chat with PI Avatar** on any PI card
2. **Page load:** PI name should appear in header (not "PI Avatar")
3. **Existing transcript:** If you chatted before, messages should reload
4. Type a message like: *"Hi! I'm interested in your lab. Can you tell me about your current projects?"*
5. PI should respond in first person, citing real papers
6. PI should ask **exactly one question** at the end

#### Avatar institution test (Bug 2 fix)

For Shapiro specifically:
- Avatar should say **Caltech** / California Institute of Technology
- Should NOT say HMC, Harvey Mudd, Brown, or any other institution
- Check: does the response mention "acoustic reporter genes" or "gas vesicles"? (real research)

### 4.5 Chemistry Report (`/report/{match_id}`)

1. From ChatPage, click **Get Chemistry Report →** (need ≥2 messages first)
2. Should navigate to `/report/{match_id}`
3. Report should show:
   - Overall chemistry score (0–100)
   - Radar chart with 5 dimensions
   - Key positives (green), key concerns (amber)
   - Recommended follow-up questions
   - Draft intro email (copy-to-clipboard)

---

## 5. API Endpoint Reference

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/survey` | Create student profile |
| `GET` | `/api/survey/{id}` | Get student by ID |
| `GET` | `/api/pi/list` | List all PIs |
| `POST` | `/api/pi/seed` | Seed from `caltech_pis.json` |
| `POST` | `/api/match/{student_id}` | Run v1.0 matching |
| `GET` | `/api/matches/{student_id}` | Get stored matches |
| `GET` | `/api/match/{match_id}` | Get single match with PI data |
| `POST` | `/api/simulate/{match_id}` | Send chat message to PI avatar |
| `POST` | `/api/evaluate/{match_id}` | Generate chemistry report |
| `GET` | `/api/report/{match_id}` | Fetch stored report |
| `POST` | `/api/upload-cv` | Upload CV file → returns `cv_text` |

Interactive docs: `http://localhost:8000/docs`

---

## 6. Known Issues & Workarounds

### Score is 50.0 for all research dimensions

**Cause:** `ANTHROPIC_API_KEY` not set.
**Fix:** `export ANTHROPIC_API_KEY=sk-ant-...` and restart uvicorn.

### `POST /api/pi/seed` returns 404

**Cause:** `data/seeds/caltech_pis.json` not found.
**Fix:** Confirm you're running uvicorn from the `backend/` directory:
```bash
cd backend && uvicorn main:app --reload --port 8000
```

### Frontend crashes on match page (TypeError: cannot read 'name' of undefined)

**Cause:** Old DB schema — matches don't have `pi` nested.
**Fix:** Re-run matching: `POST /api/match/{student_id}`. The router now always nests `pi` in the response.

### Location filter removes all results

**Cause:** After schema change to `List[str]`, old DB rows have `null` for `location_preference`.
**Fix:** Create a new student via the updated survey form. Or delete `pimatch.db` and start fresh.

### CV PDF upload returns 501

**Cause:** `pdfplumber` not installed.
**Fix:**
```bash
pip install pdfplumber --break-system-packages
```
Then restart uvicorn. TXT files work without any extra packages.

### Avatar still mentions wrong institution

**Cause:** Possibly cached DB avatar prompt from before the fix.
**Fix:** The system prompt is built fresh on every `/simulate` call — no caching. If it still happens, add the PI's institution manually to your question: *"As a Caltech professor..."* to anchor the conversation.

---

## 7. Demo Script (Golden Path)

Run this sequence for the judges:

1. **Open** `http://localhost:5173`
2. **Fill survey** as an F-1 student in Computational Biology, knowing "Páll Melsted", west coast preference
3. **Submit** → wait for matching (~10–15s with API key)
4. **Match page:** point out Pachter at top with 🔗 Indirect Connection via Páll Melsted, Anandkumar with 🇺🇸 flag
5. **Click score bars** on Pachter card → show Research rationale citing real papers
6. **Click "Chat with PI Avatar"** on Pachter
7. **Send 3 messages** — avatar asks one question per turn, cites real work
8. **Click "Get Chemistry Report →"**
9. **Report page:** show radar chart, positives, concerns, copy the draft email

Total time: ~4 minutes

---

## 8. File Locations

```
hacktech_26/
├── backend/
│   ├── main.py                  — FastAPI entry, CORS, router mounts
│   ├── database.py              — SQLite engine
│   ├── models.py                — DB table schemas
│   ├── schemas.py               — Pydantic request/response schemas
│   ├── scoring.py               — Deterministic scoring helpers
│   └── routers/
│       ├── survey.py            — /survey, /upload-cv
│       ├── pi.py                — /pi/list, /pi/seed
│       └── simulation.py        — /match, /matches, /simulate, /evaluate, /report
├── agents/
│   ├── research_match.py        — Claude: research fit scoring
│   ├── pi_avatar.py             — Claude: PI avatar system prompt builder
│   └── evaluator.py             — Claude: chemistry report generator
├── data/
│   └── seeds/
│       ├── caltech_pis.json     — 5 Caltech PI profiles
│       └── demo_student.json    — Golden demo student
└── frontend/
    └── src/
        ├── types.ts             — TypeScript interfaces
        ├── api/client.ts        — Axios API wrappers
        ├── pages/
        │   ├── SurveyPage.tsx   — Intake form (location multi-select, CV upload)
        │   ├── MatchPage.tsx    — Ranked PI list
        │   ├── ChatPage.tsx     — PI avatar chat
        │   └── ReportPage.tsx   — Chemistry report
        └── components/
            ├── PICard.tsx       — Match card with expandable score bars
            ├── ScoreRadar.tsx   — Recharts radar chart
            ├── ChatBubble.tsx   — Chat message bubble
            └── FlagBadge.tsx    — 🤝 🇺🇸 💰 🔗 badges
```

---

*Generated for Hacktech 2026 — PiMatch team*
