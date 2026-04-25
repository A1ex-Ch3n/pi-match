# PiMatch — Project Status
*Hacktech 2026 | Last updated: April 25, 2026*

---

## What Is PiMatch

PiMatch matches PhD applicants with Principal Investigators (PIs) based on research fit, funding, mentorship style, and personal connections. It targets two Hacktech tracks: **"Not So Sexy"** (real logistics problem) and **Listen Labs: Simulate Humanity** (AI avatars).

---

## MVP Checklist vs CLAUDE.md

### v1.0 — Pure Data Match ✅ COMPLETE

| Feature | Status | Notes |
|---|---|---|
| Student intake form | ✅ | Multi-section: academic background, connections, preferences, 6 sliders |
| PI database (5 Caltech PIs) | ✅ | Pachter, Anandkumar, Shapiro, Van Valen, Yue — auto-seeded on startup |
| Research fit scoring via Claude | ✅ | `agents/research_match.py` — lazy client, per-call API key read |
| Direct connection detection | ✅ | String match against `known_professors` |
| Indirect connection detection | ✅ | Co-author graph — Pachter ↔ Páll Melsted demo case |
| Location filter | ✅ | Multi-select checkboxes: west_coast / east_coast / midwest / any |
| Citizenship flag 🇺🇸 | ✅ | Anandkumar triggers this with demo student (F-1 visa) |
| Reply likelihood prediction | ✅ | Based on `papers_last_12_months` |
| Match dashboard | ✅ | Ranked cards with score accordion, flags, rationale text |

### v2.0 — PI Avatar Chat ✅ COMPLETE

| Feature | Status | Notes |
|---|---|---|
| PI avatar system prompt | ✅ | `agents/pi_avatar.py` — includes real paper DOI links per PI |
| Chat interface | ✅ | `ChatPage.tsx` — markdown rendering, clickable paper links |
| Stateful conversation | ✅ | Transcript saved to `MatchResult.transcript` |
| Avatar asks 1 question/turn | ✅ | Enforced in system prompt |
| Institution grounding | ✅ | Shapiro always says Caltech, not HMC/Brown |

### v2.5 — Conversation Evaluation ✅ COMPLETE

| Feature | Status | Notes |
|---|---|---|
| Evaluator reads transcript | ✅ | `agents/evaluator.py` — fresh Claude call, no avatar context |
| ChemistryReport (5 dimensions) | ✅ | research_alignment, mentorship_compatibility, culture_fit, communication_fit, red_flags |
| Report page with radar chart | ✅ | `ReportPage.tsx` — Recharts radar, markdown rendering throughout |
| PI introduction email draft | ✅ | Copy-to-clipboard, "review before sending" warning |

### Demo Polish ✅ COMPLETE

| Feature | Status | Notes |
|---|---|---|
| Golden demo (5 PIs + 1 student) | ✅ | Triggers indirect connection + citizenship flag automatically |
| Loading states & error handling | ✅ | Server status indicator, retry button, cold-start handling |
| Automated test suite | ✅ | `tests/run_tests.py` — 22 tests, 22/22 passing with API key |
| Frontend testing manual | ✅ | `tests/FRONTEND_TESTING.md` — 15 test cases FT01–FT15 |
| Deployed to production | ✅ | Vercel (frontend) + Render (backend) |

---

## Live Deployments

| Service | URL |
|---|---|
| **Frontend** | https://frontend-kappa-dun-61.vercel.app |
| **Backend** | https://pi-match.onrender.com |
| **API Docs** | https://pi-match.onrender.com/docs |
| **GitHub** | https://github.com/A1ex-Ch3n/pi-match |

Both auto-deploy on every push to `master`. Render free tier sleeps after 15 min — the survey page pings `/health` on load to pre-warm it.

---

## Tech Stack

| Layer | Choice | Location |
|---|---|---|
| Backend | Python + FastAPI | `backend/` |
| Database | SQLite + SQLModel | `backend/pimatch.db` |
| LLM | Anthropic Claude (`claude-sonnet-4-5`) | `agents/` |
| Frontend | React + Vite + TypeScript | `frontend/src/` |
| Styling | Tailwind CSS | inline classes |
| Charts | Recharts | `ScoreRadar.tsx` |
| Markdown | react-markdown + remark-gfm | `ChatBubble`, `PICard`, `ReportPage` |
| Hosting | Vercel + Render | production |

---

## Key Architecture Decisions

**Lazy Anthropic client** — Client created per-call (not at module import time). Setting `ANTHROPIC_API_KEY` after uvicorn starts takes effect immediately without restart.

**Auto-seed on startup** — `_auto_seed_pis()` runs in the FastAPI lifespan. No manual `POST /api/pi/seed` needed in production.

**Decoupled survey submit + match** — Survey creates the student and navigates immediately. MatchPage runs `runMatch` itself. This survives Render restarts that wipe the SQLite DB between the two calls.

**Native fetch for CV upload** — Axios's default `Content-Type: application/json` header conflicts with FormData. Native `fetch()` lets the browser set `multipart/form-data; boundary=...` correctly.

**DB reset preserves PIs** — `tests/run_tests.py` clears only `studentprofile` and `matchresult`; PI seed data survives test runs so the frontend always has data.

**Real paper links** — Each PI has 4 confirmed DOI URLs (from Semantic Scholar). The avatar is instructed to only cite papers from this list and format them as markdown links.

---

## What Is Out of Scope (per CLAUDE.md Rule #7)

- v3.0 both-side auto-conversation — explicitly excluded
- Live Semantic Scholar / NSF scraping — abstracts and grants are hand-crafted in seed JSON; `data/scraper.py` and `data/nsf.py` exist as utilities but are not wired to any endpoint
- PDF parsing reliability on Render free tier — `.txt` upload works; PDF depends on `pdfplumber` system deps

---

## How to Run Locally

```bash
# Terminal 1 — Backend
export ANTHROPIC_API_KEY="sk-ant-..."
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (talks to localhost:8000 automatically)
cd frontend && npm run dev
# → http://localhost:5173

# Terminal 3 — Test suite
python3 tests/run_tests.py
# 22/22 with API key | 20/22 without (T09 + T18 skip)
```

---

## Demo Script (5 minutes)

1. Open **https://frontend-kappa-dun-61.vercel.app**
2. Wait for **"Server ready"** green dot next to PiMatch title
3. Fill survey: F-1 visa, Computational Biology, know **"Páll Melsted"**, West Coast
4. Submit → match page loads with spinner (~15–30 s)
5. Show **Pachter #1** with 🔗 *Indirect Connection via Páll Melsted*
6. Show **Anandkumar** with 🇺🇸 *Citizenship Required*
7. Click Research score bar → rationale cites real paper topics
8. Click **Chat with PI Avatar** on Pachter
9. Send 2–3 messages — avatar cites papers as clickable DOI links
10. Click **Get Chemistry Report** — radar chart, positives, concerns, draft intro email
