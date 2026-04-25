# CLAUDE.md — PiMatch
# Project specification for all Claude Code sessions

> **READ THIS FIRST** before touching any code.

---

## Project Overview

**PiMatch** is a PhD advisor (PI) matchmaking platform for graduate school applicants.
It matches applicants with Principal Investigators (PIs) based on research fit, funding, mentorship style, connections, and more.

**Hacktech 2026** — targeting two tracks simultaneously:
- "Not So Sexy" track (solving a real, unglamorous logistics problem)
- Listen Labs: Simulate Humanity (AI avatars simulating human conversation and interaction)

**Deadline**: Sunday April 26, 2026, 9:00 AM PDT. All tech must be done by Saturday midnight.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| Database | SQLite + SQLModel |
| LLM | Anthropic Claude API (`claude-sonnet-4-5`) |
| Frontend | React + Vite + TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| PI Paper Data | Semantic Scholar API (free, no key needed) |
| PI Grant Data | NSF Awards API (free, no key needed) |
| Package managers | pip (backend) + npm (frontend) |

---

## Project File Structure

```
pi-match/
├── CLAUDE.md                    ← YOU ARE HERE — read-only reference
├── PRODUCT_SPEC.md              ← product features reference (read-only)
│
├── backend/
│   ├── main.py                  ← FastAPI app entry point
│   ├── database.py              ← SQLite setup, session management
│   ├── models.py                ← SQLModel table definitions
│   ├── schemas.py               ← Pydantic request/response schemas
│   └── routers/
│       ├── survey.py            ← POST /survey
│       ├── pi.py                ← GET /pi/list, POST /pi/seed
│       └── simulation.py        ← POST /simulate, GET /matches/{student_id}
│
├── agents/
│   ├── research_match.py        ← score_research_fit() → float + rationale
│   ├── pi_avatar.py             ← build_pi_avatar(pi_data) → system prompt string
│   ├── conversation.py          ← run_conversation() → Transcript
│   └── evaluator.py             ← evaluate_chemistry() → ChemistryReport
│
├── data/
│   ├── scraper.py               ← fetch_semantic_scholar(pi_name, institution)
│   ├── nsf.py                   ← fetch_nsf_grants(pi_name) → list[Grant]
│   ├── processor.py             ← build_pi_profile(raw_data) → PIProfile JSON
│   ├── cache/                   ← all API responses cached here as JSON files
│   └── seeds/
│       ├── caltech_pis.json     ← 5 Caltech CS/Bio PIs (hand-crafted demo data)
│       └── demo_student.json    ← golden demo student profile
│
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   │   └── client.ts        ← All fetch() calls to backend
    │   ├── pages/
    │   │   ├── SurveyPage.tsx   ← Applicant intake form
    │   │   ├── MatchPage.tsx    ← Ranked PI list + scores
    │   │   └── ChatPage.tsx     ← Conversation with PI avatar
    │   └── components/
    │       ├── PICard.tsx
    │       ├── ScoreRadar.tsx   ← Recharts radar chart
    │       ├── ChatBubble.tsx
    │       └── FlagBadge.tsx    ← 🤝 🇺🇸 💰 flag indicators
    ├── index.html
    ├── vite.config.ts
    └── package.json
```

---

## Data Schemas (Source of Truth)

Backend owns the canonical Pydantic definitions. Frontend TypeScript interfaces must mirror them exactly.

### StudentProfile

```python
class StudentProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Academic
    name: str
    gpa: float
    field_of_study: str
    research_background: str            # Free text — used for semantic matching against PI abstracts
    technical_skills: list[str]         # e.g. ["Python", "PyTorch", "wet lab"]
    years_research_experience: int
    has_publications: bool
    cv_text: Optional[str]             # Parsed from uploaded CV

    # Connections
    known_professors: list[str]         # Names of professors they personally know

    # Preferences
    preferred_research_topics: list[str]
    location_preference: str            # "west_coast" | "east_coast" | "midwest" | "any"
    citizenship_status: str             # "us_citizen" | "pr" | "f1" | "j1" | "other"
    min_stipend: Optional[int]
    preferred_lab_size: str             # "small" | "medium" | "large"

    # Sliders (all 1–5 scale)
    independence_preference: int        # 1=fully guided, 5=fully autonomous
    intervention_tolerance: int         # 1=wants high PI involvement, 5=wants minimal
    meeting_frequency_preference: int   # 1=daily, 5=monthly or less
    work_life_balance_importance: int
    industry_connections_importance: int
    publication_rate_importance: int
```

### PIProfile

```python
class PIProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Identity
    name: str
    institution: str
    department: str
    email: Optional[str]
    lab_website: Optional[str]

    # Research (from Semantic Scholar)
    semantic_scholar_id: Optional[str]
    research_areas: list[str]
    recent_abstracts: list[str]         # Last 3 years — fed into Claude for semantic matching
    co_author_ids: list[str]            # Semantic Scholar author IDs
    papers_last_12_months: int          # For reply rate prediction

    # Funding (from NSF API)
    nsf_grants: list[dict]              # [{title, amount, expiry_date, citizen_only}]
    has_active_nsf_grant: bool
    total_active_funding_usd: Optional[int]
    funding_citizen_restricted: bool    # True if any grant requires US citizenship/PR

    # Classification (manually set in seed JSON)
    tier: int                           # 1=T10, 2=T11-30, 3=T30+
    location: str                       # State code e.g. "CA"
    lab_size: int
    is_recruiting: bool

    # Avatar inputs
    pi_survey: Optional[dict]           # Stream A: PI's own answers
    student_survey_responses: list[dict] # Stream B: anonymous current-student responses

    # Cached computed values
    reply_likelihood: Optional[str]     # "high" | "medium" | "low"
```

### MatchResult

```python
class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="studentprofile.id")
    pi_id: int = Field(foreign_key="piprofile.id")

    # Dimension scores (0–100)
    research_direction_score: float     # Weight: 40% — CORE
    mentorship_style_score: float       # Weight: 20%
    funding_stability_score: float      # Weight: 15%
    culture_fit_score: float            # Weight: 10%
    technical_skills_score: float       # Weight: 10%
    location_score: float               # Filter only (not scored)

    # Connection bonuses
    is_direct_connection: bool
    is_indirect_connection: bool
    indirect_connection_via: Optional[str]

    # Flags
    citizenship_mismatch: bool

    # AI content
    research_match_rationale: str       # Claude's specific reasoning
    reply_likelihood: str               # "high" | "medium" | "low"

    # Overall
    overall_score: float

    # v2.0+
    transcript: Optional[list[dict]]    # [{"role": "pi"|"student", "content": str}]
    chemistry_report: Optional[dict]    # v2.5
```

### ChemistryReport (v2.5)

```python
class ChemistryReport(BaseModel):
    overall_score: float

    dimension_scores: dict              # keys: research_alignment, mentorship_compatibility,
                                        #        culture_fit, communication_fit, red_flags
                                        # red_flags is inverted: 100 = no red flags

    dimension_rationale: dict           # same keys, 1–2 sentence explanation each
    key_positives: list[str]           # 2–3 specific transcript moments showing fit
    key_concerns: list[str]            # 2–3 unresolved issues
    recommended_questions: list[str]
    pi_introduction_draft: str         # warm intro email draft for applicant to review
```

---

## API Endpoints

Backend runs on `http://localhost:8000`. Frontend calls `http://localhost:8000/api/*`.

```
POST   /api/survey                 → Submit student intake form → StudentProfile
GET    /api/pi/list                → List all PIs → list[PIProfile]
POST   /api/pi/seed                → Seed from JSON file
POST   /api/match/{student_id}     → Run v1.0 matching → list[MatchResult]
POST   /api/simulate/{match_id}    → Run v2.0 PI avatar chat session → MatchResult with transcript
POST   /api/evaluate/{match_id}    → Run v2.5 evaluation → ChemistryReport
GET    /api/matches/{student_id}   → Get all match results for a student
GET    /api/report/{match_id}      → Get chemistry report + intro draft
```

---

## Agent Functions (agents/)

### research_match.py — HIGHEST PRIORITY, implement first

```python
def score_research_fit(
    student_background: str,       # StudentProfile.research_background + cv_text
    pi_abstracts: list[str],       # PIProfile.recent_abstracts
    pi_research_areas: list[str]
) -> tuple[float, str]:
    """
    Call Claude to compare student background against PI's recent abstracts.
    Output must be specific — cite actual paper topics, not generic phrases.
    
    Prompt must end with: "Respond ONLY with valid JSON: {"score": float, "rationale": str}"
    Score range: 0–100.
    Rationale: 2–3 sentences citing specific overlap with PI's actual work.
    Wrap json.loads() in try/except with fallback score of 50.
    """
```

### pi_avatar.py

```python
def build_pi_avatar(pi_profile: PIProfile) -> str:
    """
    Returns a system prompt string for the PI avatar.
    
    Must include:
    - PI's research areas and specific recent papers
    - PI survey responses (Stream A) — official voice
    - Student survey responses (Stream B) — lived reality, kept anonymous
    - Funding and lab size context
    
    Avatar rules (embed in system prompt):
    - Speak in first person as the PI
    - Be specific — cite real papers and grants
    - Ask the applicant exactly 1 question per response about their fit
    - Surface what the PI cares about most (from survey)
    - When uncertain, say so — never fabricate
    """
```

### evaluator.py

```python
def evaluate_chemistry(
    transcript: list[dict],
    student_profile: StudentProfile,
    pi_profile: PIProfile,
    v1_match_result: MatchResult
) -> ChemistryReport:
    """
    Fresh Claude call — NO shared context with the PI avatar.
    
    Reads full transcript and scores 5 dimensions:
    - research_alignment
    - mentorship_compatibility (independence/intervention match)
    - culture_fit
    - communication_fit
    - red_flags (inverted: 100 = no red flags)
    
    Also extracts key_positives, key_concerns, recommended_questions,
    and drafts a pi_introduction_draft email.
    
    Output: valid JSON matching ChemistryReport schema.
    """
```

---

## External APIs

### Semantic Scholar
```
Base URL: https://api.semanticscholar.org/graph/v1

Search author:
  GET /author/search?query={name}&fields=authorId,name,affiliations

Get papers (filter to last 3 years client-side):
  GET /author/{authorId}/papers?fields=title,abstract,year&limit=20

Get co-authors:
  GET /author/{authorId}?fields=coAuthors

Rate limit: 100 req / 5 min — cache every response to data/cache/{authorId}.json
```

### NSF Awards API
```
Base URL: https://api.nsf.gov/services/v1/awards.json

Active grants query:
  GET ?pdPIName={last_name}&expDateStart=01/01/2024
      &printFields=id,title,awardeeName,piFirstName,piLastName,fundsObligatedAmt,expDate

Parse: title, fundsObligatedAmt (amount), expDate
Coverage: ~70% of CS faculty. Does not cover NIH, DARPA, or industry.
Cache responses to data/cache/nsf_{lastname}.json
```

### Anthropic Claude API
```python
import anthropic, os, json

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
text = response.content[0].text

# For all structured outputs:
# 1. End every prompt with: "Respond ONLY with valid JSON. No explanation."
# 2. Always wrap in try/except json.loads() with a sensible fallback
```

---

## Matching Score Weights (v1.0)

```python
SCORE_WEIGHTS = {
    "research_direction": 0.40,   # Claude semantic match — soul of the product
    "mentorship_style":   0.20,
    "funding_stability":  0.15,
    "technical_skills":   0.10,
    "culture_fit":        0.10,
    "reply_likelihood":   0.05,
}

# Connection overrides (applied after weighted score):
# Direct connection  → pin to top of list + 🤝 label
# Indirect connection → +10 pts to overall_score + 🔗 label + indirect_connection_via name

# Pre-score filters (remove PI from results entirely if):
# Location mismatch: student has preference AND PI.location doesn't match

# Flags (don't remove — just display):
# Citizenship: funding_citizen_restricted=True AND student is not us_citizen/pr → 🇺🇸 flag
```

---

## Demo Seed Data

### `data/seeds/caltech_pis.json` — 5 real Caltech PIs

Hand-craft using public information only. Each PI entry must include:
- `name`, `institution` ("Caltech"), `department`, `tier` (1), `location` ("CA")
- `research_areas`: 3–5 keywords from their lab website
- `recent_abstracts`: 3–5 actual paper abstracts (from Google Scholar)
- `nsf_grants`: from NSF Reporter if available, else empty list
- `is_recruiting`: true (for demo)
- `lab_size`: approximate from lab website
- `pi_survey`: plausible answers based on public profile
- `student_survey_responses`: 2–3 fictional but realistic anonymous responses

### `data/seeds/demo_student.json` — golden demo student

```json
{
  "name": "Demo Student",
  "gpa": 3.9,
  "field_of_study": "Computational Biology",
  "research_background": "ML methods for protein structure prediction and genomics...",
  "citizenship_status": "f1",
  "known_professors": ["[name of a co-author of one of the 5 PIs]"],
  "independence_preference": 4,
  "location_preference": "west_coast"
}
```

The demo student must trigger at least:
- One indirect connection (via known_professors co-author match)
- One citizenship flag (🇺🇸) on at least one PI

---

## MVP Checklist

### v1.0 — Pure Data Match (Target: Saturday 6AM)
- [ ] Student intake form (frontend)
- [ ] PI database seeded with 5 Caltech PIs
- [ ] Semantic Scholar data fetched and cached
- [ ] NSF grant data fetched and cached
- [ ] Research fit scoring via Claude (`research_match.py`)
- [ ] Direct connection detection (string match)
- [ ] Indirect connection detection (co-author graph)
- [ ] Location filter
- [ ] Citizenship flag
- [ ] Reply likelihood prediction
- [ ] Match dashboard: ranked list + scores + flags

### v2.0 — PI Avatar Chat (Target: Saturday 12PM)
- [ ] PI avatar system prompt built from survey + student responses
- [ ] Chat interface (ChatPage.tsx)
- [ ] Stateful conversation via backend
- [ ] Avatar proactively asks 1 question per turn
- [ ] Transcript saved to MatchResult

### v2.5 — Conversation Evaluation (Target: Saturday 6PM)
- [ ] Evaluator agent reads transcript
- [ ] ChemistryReport generated
- [ ] Match report page with radar chart
- [ ] PI introduction email draft

### Demo Polish (Target: Saturday midnight)
- [ ] Golden demo: 5 PIs + 1 student, full end-to-end run
- [ ] Loading states and error handling
- [ ] Devpost description
- [ ] README.md

---

## Non-Negotiable Rules

1. **Research direction match is the soul.** Always the highest-weight dimension. Output must be specific — cite actual papers and topics, never generic phrases.

2. **Avatars never fabricate.** If the PI survey didn't cover something, the avatar says "I'm not sure — you'd want to ask Professor X directly."

3. **Nothing auto-sends to PIs.** The intro email is a draft. The applicant reviews and sends manually.

4. **Grad student survey responses are externally anonymous.** Never expose individual responses via any API endpoint.

5. **Cache all external API calls.** Write every Semantic Scholar and NSF response to `data/cache/`. Rate limits will hit during demo.

6. **All AI outputs are structured JSON.** Every Claude call producing scores or reports must output JSON. Always use try/except with a fallback.

7. **v3.0 is NOT in scope.** Do not implement the both-side auto-conversation. It is future vision only.

---

## Environment

```bash
# Backend
pip install fastapi uvicorn sqlmodel anthropic requests python-multipart --break-system-packages
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss recharts axios
npm run dev   # http://localhost:5173

# .env (root directory)
ANTHROPIC_API_KEY=your_key_here
```

---

*Last updated: April 25, 2026*
