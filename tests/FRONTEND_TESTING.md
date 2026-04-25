# PiMatch Frontend Testing Manual

> Run this after the backend test suite passes (22/22).
> Open DevTools (F12) → Console tab before starting — keep it visible throughout.

---

## Setup

1. Backend running with API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   cd backend && uvicorn main:app --reload --port 8000
   ```

2. Frontend running:
   ```bash
   cd frontend && npm run dev
   ```

3. Open `http://localhost:5173` in Chrome or Firefox.

---

## FT01 — Survey Form: Basic Submission

**Goal:** Fill out the demo student profile and reach the match page.

1. Open `http://localhost:5173` — confirm the survey form loads with no console errors.
2. Fill in the following fields:

   | Field | Value |
   |-------|-------|
   | Full Name | `Demo Student` |
   | GPA | `3.9` |
   | Years of Research Experience | `3` |
   | Field of Study | `Computational Biology` |
   | Research Background | `I develop ML methods for protein structure prediction and single-cell genomics. I have experience with graph neural networks, transformer models, and bioinformatics pipelines.` |
   | Technical Skills | `Python, PyTorch, R, CRISPR, scRNA-seq` |
   | Has Publications | ✅ checked |
   | Professors You Know | `Páll Melsted` |
   | Preferred Research Topics | `computational biology, genomics, machine learning` |
   | Location | ✅ West Coast |
   | Citizenship Status | F-1 Visa |
   | Preferred Lab Size | Medium (6–12) |

3. Leave sliders at default (all 3), minimum stipend blank.
4. Click **Find My PI Matches →**.

**Expected:**
- Button shows a loading/spinner state.
- After 10–30 seconds (Claude API), navigates to `/matches/{id}`.
- No console errors.

**Fail if:** Page hangs indefinitely, shows a red error box, or console shows an uncaught exception.

---

## FT02 — Survey Form: Sliders

**Goal:** Verify all 6 sliders work and display their value.

1. Go back to `http://localhost:5173`.
2. Drag each slider end-to-end:
   - Independence Preference: 1 → 5 → back to 4
   - Intervention Tolerance: 1 → 5 → back to 4
   - Meeting Frequency: 1 → 5 → back to 3
   - Work-Life Balance: 1 → 5 → back to 4
   - Industry Connections: 1 → 5 → back to 2
   - Publication Rate: 1 → 5 → back to 4

**Expected:** Each slider shows its numeric value (1–5) as you drag. Value updates visually.

---

## FT03 — Survey Form: CV Upload

**Goal:** Upload a plain-text CV and confirm the text is extracted.

1. Create a small text file on your desktop: `test_cv.txt` containing:
   ```
   Jane Doe — Computational Biology PhD Candidate
   Skills: Python, PyTorch, scRNA-seq
   Papers: 2 published in Nature Methods
   ```
2. On the survey form, click **📎 Upload CV** (or the file input).
3. Select `test_cv.txt`.

**Expected:**
- Filename appears next to the upload button.
- The CV text textarea auto-fills with the file's content.
- No error message shown.

**Also test:** Try uploading a `.jpg` or other unsupported type.

**Expected:** Error message shown inline (e.g. "Unsupported file type"). Textarea stays empty.

---

## FT04 — Survey Form: Location Multi-select

**Goal:** Confirm location checkboxes work correctly.

1. On the survey form, check **West Coast**.
2. Also check **East Coast** — both should be selected simultaneously.
3. Now check **No preference** — all other options should deselect, leaving only "No preference" checked.
4. Check **Midwest** — "No preference" should deselect automatically.

**Expected:** Selecting "No preference" clears all others; selecting any region clears "No preference".

---

## FT05 — Match Page: Cards and Badges

**Goal:** Verify the ranked match list displays correctly.

After FT01, you should be on `/matches/{id}`. If not, resubmit the survey.

1. **Count:** Confirm 5 PI cards are displayed.
2. **Ranking:** Cards are sorted by overall score (highest first), with any direct connections pinned to the top.
3. **Pachter card — Indirect Connection badge:**
   - Find the Lior Pachter card.
   - Confirm it shows a 🔗 **Indirect Connection via Páll Melsted** badge.
4. **Anandkumar card — Citizenship badge:**
   - Find the Anima Anandkumar card.
   - Confirm it shows a 🇺🇸 **Citizenship Required** badge.
5. **Funding badge:**
   - Any PI with an active NSF grant shows 💰 **Active Funding**.
6. **Reply likelihood:**
   - Each card shows a reply badge: green = high, amber = medium, red = low.
7. **Research area tags:**
   - Each card shows up to 4 gray research area tags below the PI name.

**Fail if:** Any badge is missing for the conditions above, or scores are all 0.

---

## FT06 — Match Page: Score Accordion

**Goal:** Verify clickable score bars expand and show rationale.

1. On any PI card, find the row that says **"Click any score to see why ▾"**.
2. Click the **Research** score bar.
   - Bar expands to show a 2–3 sentence rationale.
   - Rationale mentions specific paper topics (not just "strong overlap").
   - Score color: green (70+), amber (50–69), red (<50).
3. Click it again — bar collapses.
4. Click **Mentorship**, **Funding**, **Culture**, **Skills** bars one at a time.
   - Each expands independently.
   - Multiple can be open at once.

**Fail if:** Click does nothing, rationale is blank, or multiple bars don't stay open simultaneously.

---

## FT07 — Match Page: Rerun Matching

**Goal:** Confirm the Rerun button re-triggers matching and updates results.

1. Click **Rerun Matching** at the top of the match page.
2. Button should show **"Rerunning…"** while waiting.
3. After 10–30 seconds, match list refreshes.

**Expected:** Same 5 PIs, potentially with slightly different AI scores. No crash.

---

## FT08 — Chat Page: Sending Messages

**Goal:** Have a conversation with a PI avatar and verify it behaves correctly.

1. On the Pachter card, click **Chat with PI Avatar**.
2. Confirm the page header shows **Lior Pachter** (not "PI Avatar" or another name).
3. Confirm the header subtitle shows department and institution (**Caltech**).
4. Type: `Hi! I'm interested in your lab. Can you tell me about your current projects?`
5. Press **Enter** (or click **Send**).

**Expected:**
- Your message appears immediately on the right side (violet background).
- Typing indicator (3 animated dots) appears on the left.
- After 5–15 seconds, PI response appears on the left (gray background).
- Response mentions real research (genomics, sequencing, RNA, etc.) — not generic filler.
- Response ends with **exactly one question** directed at you.

6. Send a second message: `I've been working on single-cell RNA-seq analysis using variational autoencoders.`

**Expected:** PI responds again and asks one more question.

---

## FT09 — Chat Page: Avatar Institution Check (Shapiro)

**Goal:** Confirm Shapiro avatar identifies as Caltech, not a previous institution.

1. Go back to matches (`← Back` in the chat header).
2. Click **Chat with PI Avatar** on the **Mikhail Shapiro** card.
3. Send: `Hi! Tell me about your research and your lab at Caltech.`

**Expected:**
- Response mentions **Caltech** or **California Institute of Technology**.
- Response does **NOT** mention HMC, Harvey Mudd, Brown, or any other institution.
- Response references real Shapiro lab topics (acoustic reporter genes, gas vesicles, ultrasound imaging, MRI).

---

## FT10 — Chat Page: Transcript Persistence

**Goal:** Confirm chat history reloads when you revisit the page.

1. After FT08, note the number of messages in the Pachter chat (should be 4: 2 student + 2 PI).
2. Navigate away: click **← Back** to matches.
3. Click **Chat with PI Avatar** on Pachter again.

**Expected:** All previous messages reload — same 4 messages, in the same order. No blank page.

---

## FT11 — Chat Page: Get Chemistry Report Button

**Goal:** Confirm the report button is gated on message count and navigates correctly.

1. Open a fresh chat (one with 0 messages — pick a PI you haven't chatted with yet).
2. Confirm **Get Chemistry Report →** button is **grayed out / disabled**.
3. Send one message. Button still disabled (only 1 exchange so far... confirm at 2 messages).
4. After the PI responds (2 total messages), confirm the button **becomes active**.
5. Click **Get Chemistry Report →**.
   - Button shows **"Evaluating…"** state.
   - After 10–20 seconds, navigates to `/report/{matchId}`.

---

## FT12 — Report Page: Full Display

**Goal:** Verify all sections of the chemistry report render correctly.

After FT11, you should be on the report page.

1. **Overall Score:** Large violet number (0–100) displayed center-top.
2. **Radar Chart:** 5-axis chart with labels — Research, Mentorship, Culture, Communication, No Red Flags. Chart should be filled, not empty.
3. **Dimension Breakdown:** Below the chart, 5 rows each with:
   - Dimension name
   - Score (e.g. "72 / 100")
   - Colored progress bar
   - 1–2 sentence rationale
4. **Key Positives** (left, emerald/green background): 2–3 bullet points with ✅ icons.
5. **Key Concerns** (right, amber background): 2–3 bullet points with ⚠️ icons.
6. **Questions to Ask:** Numbered list of 3–4 follow-up questions.
7. **Introduction Email Draft:**
   - 3–4 sentences of email text in monospace/gray background.
   - **Copy** button — click it.
   - Button briefly shows **"Copied!"**, then reverts.
   - Paste somewhere to confirm the text is on the clipboard.

---

## FT13 — Navigation Flow

**Goal:** Confirm all back/forward navigation links work.

| From | Action | Expected destination |
|------|--------|----------------------|
| Survey `/` | Submit form | `/matches/{id}` |
| Match page | Click "← New Search" | `/` (survey, blank) |
| Match page | Click "Chat with PI Avatar" | `/chat/{matchId}` |
| Chat page | Click "← Back" | `/matches/{studentId}` |
| Chat page | Click "Get Chemistry Report →" | `/report/{matchId}` |
| Report page | Click "← Back to Chat" | `/chat/{matchId}` |

---

## FT14 — Error States

**Goal:** Verify the app handles errors gracefully.

1. **Backend down:** Stop uvicorn. Submit the survey form.
   - **Expected:** Red error box appears below the form. No crash.
   - Restart uvicorn before continuing.

2. **Direct URL with bad ID:** Visit `http://localhost:5173/matches/99999`.
   - **Expected:** Empty state or error message, not a blank white page or console crash.

3. **Report before transcript:** Visit `/report/{matchId}` for a match with no transcript.
   - **Expected:** Error message or redirect, not a crash.

---

## FT15 — Console Check

**Goal:** Confirm there are no rogue errors after the full golden path.

1. Open DevTools → Console.
2. Clear the console.
3. Run the full golden path: Survey → Matches → Chat (2 messages) → Report.
4. Inspect the console.

**Expected:** No red errors. Yellow warnings about React StrictMode double-rendering are acceptable. Network errors related to optional fields (e.g. lab_website) are acceptable if handled gracefully.

---

## Summary Checklist

| Test | What it checks |
|------|----------------|
| FT01 | Survey submits, navigates to match page |
| FT02 | All 6 sliders work |
| FT03 | CV upload (.txt) extracts text; bad file type shows error |
| FT04 | Location multi-select logic (No preference clears others) |
| FT05 | 5 cards, 🔗 badge on Pachter, 🇺🇸 badge on Anandkumar |
| FT06 | Score bars expand/collapse, rationale is specific |
| FT07 | Rerun Matching button works |
| FT08 | Chat sends, PI responds in character, asks one question |
| FT09 | Shapiro avatar says Caltech, not HMC/Harvey Mudd/Brown |
| FT10 | Chat history persists across page visits |
| FT11 | Report button disabled < 2 messages, navigates after evaluate |
| FT12 | Report shows radar chart, scores, positives, concerns, email + copy |
| FT13 | All nav links go to correct routes |
| FT14 | Error states handled gracefully (no crashes) |
| FT15 | No red console errors on golden path |
