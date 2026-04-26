# PiMatch — Local Setup & Testing Guide
*Branch: integration/frontend-redesign*

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- An Anthropic API key (`sk-ant-...`)

---

## First-Time Setup

### 1. Clone the repo

```bash
git clone https://github.com/A1ex-Ch3n/pi-match.git -b integration/frontend-redesign
cd pi-match
```

### 2. Install backend dependencies

```bash
pip install fastapi uvicorn sqlmodel anthropic requests python-multipart --break-system-packages
```

### 3. Install frontend dependencies

```bash
cd frontend && npm install && cd ..
```

---

## Running Locally

Open **two terminals**.

### Terminal 1 — Backend

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cd backend
uvicorn main:app --reload --port 8000
```

Expected startup output:
```
INFO:     Application startup complete.
[startup] Seeded N new PI(s) (0 duplicate(s) skipped)
```

Verify it's healthy:
```bash
curl http://localhost:8000/health
# → {"status": "ok", "api_key_configured": true}
```

If `api_key_configured` is `false`, the key wasn't picked up — re-export and restart.

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
# → http://localhost:5173
```

Open **http://localhost:5173** in your browser. The status dot in the header should turn green ("Server ready").

---

## Demo Flow (End-to-End Test)

### Step 1 — Submit a student profile

Fill out the survey with this profile to trigger all demo features:

| Field | Value |
|---|---|
| Name | Any name |
| GPA | 3.9 |
| Field of Study | Computational Biology |
| Research Background | *ML methods for protein structure prediction and genomics. Experience with PyTorch and single-cell RNA-seq analysis.* |
| Technical Skills | `Python, PyTorch, genomics, bioinformatics` |
| Known Professors | `Páll Melsted` ← triggers indirect connection with Pachter |
| Location | West Coast |
| Citizenship | F-1 visa ← triggers citizenship flag on Anandkumar |

Submit and wait for the match page (~10–20 seconds with API key).

### Step 2 — Verify match results

- Pachter should appear near the top with a 🔗 **Indirect connection via Páll Melsted** badge
- Anandkumar should show a 🇺🇸 **Citizenship Required** flag
- Click any score bar to expand the rationale — it should cite specific paper topics

### Step 3 — Chat with a PI Avatar

- Click **Chat with PI Avatar** on any matched PI
- Send 2–3 messages
- The avatar should ask one question per response and reference real papers as links
- Paper links should open the correct DOI page in a new tab

### Step 4 — Chemistry Report

- After 4+ messages, click **Get Chemistry Report**
- Radar chart, key positives/concerns, and intro email draft should all appear

---

## Running the Automated Test Suite

```bash
# Make sure the backend is running with the API key set first
python3 tests/run_tests.py
```

Expected: **21/22 passing** (T02 skips when PIs are already seeded — this is normal).

If T08 (matching) fails, check that the backend is running and the API key is set.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Status dot is amber "API key not set" | Re-export `ANTHROPIC_API_KEY` and restart uvicorn |
| "Could not reach the server" | Backend isn't running — start uvicorn in Terminal 1 |
| Status dot stays on "Waking server…" | Render is cold-starting (production only) — wait 30s |
| Only 1 PI in match results | Run a fresh survey — stale DB may have leftover matches |
| Paper links open wrong page | Backend hot-reload may be needed — save any backend file to trigger it |
| `NaN` in URL | Clear browser localStorage: `localStorage.clear()` in DevTools console |

---

## Production Deployments

| Service | URL | Auto-deploys from |
|---|---|---|
| Frontend | https://frontend-kappa-dun-61.vercel.app | `master` branch |
| Backend | https://pi-match.onrender.com | `master` branch |

To make this branch live, merge `integration/frontend-redesign` into `master` and push.
