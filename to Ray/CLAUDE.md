# CLAUDE.md — PiMatch (Ray's Session)
# Read this before writing any code.

---

## What This Project Is

**PiMatch** — PhD advisor matchmaking platform. Matches grad school applicants with PIs based on research fit, funding, mentorship style, and connections. Built in one weekend for Hacktech 2026.

**Your role**: You are responsible for three files only. Do not touch anything outside this list:
1. `data/seeds/caltech_pis.json` — hand-crafted demo data for 5 real Caltech PIs
2. `agents/research_match.py` — Claude-powered semantic research fit scoring
3. `agents/pi_avatar.py` — builds PI avatar system prompt from profile data

Alex owns all backend, frontend, and matching logic. He will call your functions directly.

---

## Your File Responsibilities

```
pi-match/
├── data/
│   └── seeds/
│       └── caltech_pis.json        ← YOU OWN THIS
└── agents/
    ├── research_match.py           ← YOU OWN THIS
    └── pi_avatar.py               ← YOU OWN THIS (after research_match is done)
```

Do not modify any other files.

---

## Task 1: `data/seeds/caltech_pis.json`

**Priority: HIGHEST. Alex cannot test anything without this.**

Create a JSON array of 5 real Caltech PIs. Use only publicly available information.

### Required schema for each PI

```json
{
  "name": "string — full name",
  "institution": "Caltech",
  "department": "string",
  "email": "string or null",
  "lab_website": "string or null",
  "tier": 1,
  "location": "CA",
  "lab_size": "integer — approximate number of current grad students",
  "is_recruiting": true,

  "research_areas": ["3–5 keyword strings from their lab website"],

  "recent_abstracts": [
    "Full abstract text of paper 1 (last 3 years)",
    "Full abstract text of paper 2",
    "Full abstract text of paper 3"
  ],

  "nsf_grants": [
    {
      "title": "Grant title",
      "amount": 500000,
      "expiry_date": "YYYY-MM-DD",
      "citizen_only": false
    }
  ],
  "has_active_nsf_grant": true,
  "total_active_funding_usd": 500000,
  "funding_citizen_restricted": false,

  "semantic_scholar_id": "string or null",
  "co_author_ids": [],
  "papers_last_12_months": 3,
  "reply_likelihood": null,

  "pi_survey": {
    "research_philosophy": "string",
    "what_i_look_for": "string",
    "typical_student_week": "string",
    "mentorship_approach": "string",
    "funding_outlook": "string",
    "advice_to_applicants": "string"
  },

  "student_survey_responses": [
    {
      "lab_culture": "string",
      "meeting_frequency": "string",
      "independence": "string",
      "wished_i_knew": "string",
      "thrives_here": "string",
      "struggles_here": "string"
    }
  ]
}
```

### Where to find the data

| Field | Source |
|---|---|
| `recent_abstracts` | Google Scholar → search PI name → copy abstracts from last 3 years |
| `nsf_grants` | nsf.gov/awardsearch → search PI last name → look for active awards |
| `lab_size` | PI's lab website → Team page → count grad students |
| `pi_survey` | Infer from lab website, published interviews, public talks — plausible is fine |
| `student_survey_responses` | Fictional but realistic — 2 responses per PI minimum |

### Hard requirements for the demo

- At least 1 PI must have `"funding_citizen_restricted": true` in their grants — this triggers the 🇺🇸 citizenship flag
- At least 1 PI must be a known co-author of someone the demo student knows — ask Alex what name to use for the demo student's `known_professors` field, then make one PI share that co-author
- The 5 PIs must span different research sub-areas (not all the same field)
- All `recent_abstracts` must be real text from real papers, not invented

---

## Task 2: `agents/research_match.py`

**Priority: HIGH. This is the core AI function. Alex calls it inside his matching algorithm.**

### Function signature — do not change this

```python
def score_research_fit(
    student_background: str,       # From student's research_background + cv_text fields
    pi_abstracts: list[str],       # PIProfile.recent_abstracts
    pi_research_areas: list[str]   # PIProfile.research_areas
) -> tuple[float, str]:
    """
    Returns (score: float 0–100, rationale: str)
    """
```

### Implementation requirements

1. Call Claude API with a prompt that reads PI's abstracts and compares to student's background
2. Output must be specific — rationale must cite actual paper topics and the student's specific background. Generic output ("your interests seem related") is a failure.
3. Claude must return JSON: `{"score": float, "rationale": str}`
4. Always wrap `json.loads()` in try/except — fallback: return `(50.0, "Unable to compute research fit.")`

### Full implementation template

```python
import anthropic
import json
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def score_research_fit(
    student_background: str,
    pi_abstracts: list[str],
    pi_research_areas: list[str]
) -> tuple[float, str]:
    
    abstracts_block = "\n\n---\n\n".join(pi_abstracts)
    
    prompt = f"""You are evaluating the research fit between a PhD applicant and a principal investigator (PI).

PI's declared research areas:
{', '.join(pi_research_areas)}

PI's recent papers (last 3 years) — abstracts only:
{abstracts_block}

Applicant's research background and experience:
{student_background}

Task: Score the fit from 0 to 100. Be specific and grounded.
- GOOD rationale: "Your work on protein structure prediction using graph neural networks directly parallels Dr. Chen's 2024 paper on geometric deep learning for molecular dynamics."
- BAD rationale: "Your interests appear to align with the PI's research areas."

The rationale must mention specific topics from the PI's abstracts and specific aspects of the student's background.

Respond ONLY with valid JSON, no explanation outside the JSON:
{{"score": <float 0-100>, "rationale": "<2-3 sentences>"}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        data = json.loads(response.content[0].text.strip())
        score = float(data["score"])
        rationale = str(data["rationale"])
        return score, rationale
    except Exception as e:
        return 50.0, "Unable to compute research fit score."
```

### How to test it independently

```python
# In agents/research_match.py, at the bottom:
if __name__ == "__main__":
    score, rationale = score_research_fit(
        student_background="I study ML methods for protein structure prediction, specifically using graph neural networks on molecular dynamics data.",
        pi_abstracts=[
            "We present a geometric deep learning framework for predicting protein conformational changes...",
            "Our work applies equivariant neural networks to molecular simulation trajectories..."
        ],
        pi_research_areas=["computational biology", "geometric deep learning", "molecular dynamics"]
    )
    print(f"Score: {score}")
    print(f"Rationale: {rationale}")
```

Run with: `python agents/research_match.py`

---

## Task 3: `agents/pi_avatar.py`

**Priority: MEDIUM. Do this after Tasks 1 and 2 are done and tested.**

### Function signature — do not change this

```python
def build_pi_avatar(pi_profile: dict) -> str:
    """
    Returns: system prompt string that makes Claude act as this PI.
    """
```

### Implementation requirements

The returned system prompt must make Claude:
- Speak in first person as the PI
- Be specific — reference actual papers by topic, actual grants by title
- Ask the applicant **exactly 1 question per response** about their fit or background
- Bring up things the PI cares about (from `pi_survey`) naturally during the conversation
- Blend the official voice (`pi_survey`) with the lived reality from `student_survey_responses` (paraphrase anonymously — never quote directly)
- Say "I'm not sure about that — you'd want to ask me directly" when a topic is not in its knowledge base
- Never fabricate specific numbers, deadlines, or paper titles not present in the profile

### Implementation template

```python
def build_pi_avatar(pi_profile: dict) -> str:
    
    name = pi_profile["name"]
    institution = pi_profile["institution"]
    department = pi_profile["department"]
    research_areas = ", ".join(pi_profile.get("research_areas", []))
    abstracts = pi_profile.get("recent_abstracts", [])
    pi_survey = pi_profile.get("pi_survey", {})
    student_responses = pi_profile.get("student_survey_responses", [])
    
    # Summarize student survey anonymously
    culture_signals = []
    for r in student_responses:
        if r.get("lab_culture"):
            culture_signals.append(r["lab_culture"])
        if r.get("thrives_here"):
            culture_signals.append(f"Students who thrive: {r['thrives_here']}")
    culture_summary = " ".join(culture_signals[:3])
    
    system_prompt = f"""You are Professor {name} from {department} at {institution}.
    
You are having a conversation with a PhD applicant who is considering joining your lab.

YOUR RESEARCH:
Your main research areas are: {research_areas}

Recent work from your lab:
{chr(10).join(f'- {a[:300]}...' for a in abstracts[:4])}

YOUR MENTORSHIP STYLE (from your own description):
- Philosophy: {pi_survey.get('research_philosophy', 'Not specified')}
- What you look for: {pi_survey.get('what_i_look_for', 'Not specified')}
- Typical student week: {pi_survey.get('typical_student_week', 'Not specified')}
- Your approach: {pi_survey.get('mentorship_approach', 'Not specified')}
- Funding: {pi_survey.get('funding_outlook', 'Not specified')}

LAB CULTURE (based on current student feedback, summarized):
{culture_summary}

RULES YOU MUST FOLLOW:
1. Always speak in first person as Professor {name}. You ARE this person.
2. Be specific — reference your actual research topics, not generic phrases.
3. At the end of EVERY response, ask the applicant exactly ONE question about their background, interests, or fit with your lab.
4. Proactively bring up things you care about from the survey above — don't wait to be asked.
5. If asked something you don't know or that's not in your profile, say: "I'm not sure about that off the top of my head — it would be best to discuss this directly when we meet."
6. Never invent paper titles, grant amounts, or student names not present in this profile.
7. You are warm but honest. You care about fit as much as the applicant does."""

    return system_prompt
```

---

## Claude API Reference

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Standard call
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "your prompt here"}]
)
text = response.content[0].text

# For JSON outputs:
# - End prompt with: "Respond ONLY with valid JSON. No explanation."
# - Always: json.loads(text.strip()) inside try/except
```

Set the API key in your shell before running anything:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

---

## Install Dependencies

```bash
pip install anthropic --break-system-packages
```

---

## What Alex Expects From You

When Alex runs his matching algorithm, he will call:

```python
from agents.research_match import score_research_fit
score, rationale = score_research_fit(student_bg, abstracts, areas)
# score: float 0–100
# rationale: 2–3 sentences, specific

from agents.pi_avatar import build_pi_avatar
system_prompt = build_pi_avatar(pi_dict)
# system_prompt: string, ready to pass to Claude as system message
```

And he will load your seed data with:
```python
import json
with open("data/seeds/caltech_pis.json") as f:
    pis = json.load(f)
# pis: list of dicts matching the schema above
```

Do not change function names, signatures, or return types.

---

## Priority Order

1. `data/seeds/caltech_pis.json` — Alex is blocked without this
2. `agents/research_match.py` — Core scoring function, Alex integrates this into v1.0
3. `agents/pi_avatar.py` — Needed for v2.0, start after #1 and #2 pass their tests

---

*This file is your single source of truth. Read it before starting each work session.*
