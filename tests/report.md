# PiMatch Test Report
Generated: 2026-04-25 15:31:05

## Summary
- Total: 22
- Passed: 5
- Failed: 2
- Skipped: 15

## Results

| ID | Test | Status | Detail |
|----|------|--------|--------|
| T01 | Health check | ✅ PASS |  |
| T02 | PI list empty | ⏭️ SKIP | SKIP — 12 PIs already seeded (PI data is preserved between runs) |
| T03 | Seed PIs | ✅ PASS |  |
| T04 | PI list populated | ❌ FAIL | Got 200 with 12 PIs |
| T05 | PI institutions correct | ⏭️ SKIP | SKIP (depends on T04) |
| T06 | Create student | ✅ PASS |  |
| T07 | Get student | ✅ PASS |  |
| T08 | Run matching | ❌ FAIL | Got 200 with 6 results |
| T09 | Research scores not all 50 | ⏭️ SKIP | SKIP (depends on T08) |
| T10 | Rationales are specific | ⏭️ SKIP | SKIP (depends on T08) |
| T11 | Indirect connection (Pachter) | ⏭️ SKIP | SKIP (depends on T08) |
| T12 | Citizenship flag (Anandkumar) | ⏭️ SKIP | SKIP (depends on T08) |
| T13 | PI nested in match | ⏭️ SKIP | SKIP (depends on T08) |
| T14 | Get single match | ⏭️ SKIP | SKIP (depends on T08) |
| T15 | Get matches list | ⏭️ SKIP | SKIP (depends on T08) |
| T16 | Chat simulate | ⏭️ SKIP | SKIP (depends on T08) |
| T17 | Avatar says Caltech (Shapiro) | ⏭️ SKIP | SKIP (depends on T08) |
| T18 | Avatar asks a question | ⏭️ SKIP | SKIP (depends on T16) |
| T19 | Transcript persists | ⏭️ SKIP | SKIP (depends on T16) |
| T20 | CV upload txt | ✅ PASS |  |
| T21 | Chemistry evaluate | ⏭️ SKIP | SKIP (depends on T16) |
| T22 | Report fetch | ⏭️ SKIP | SKIP (depends on T21) |

## Failures Detail

### T04 — PI list populated
Expected: 200 with 5 PIs
Got: [{'id': 1, 'name': 'Lior Pachter', 'institution': 'Caltech', 'department': 'Computing and Mathematical Sciences / Biology', 'email': None, 'lab_website': 'https://pachterlab.github.io', 'semantic_scho

### T08 — Run matching
Expected: 200 with 5 MatchResults
Got: [{'id': 1, 'student_id': 1, 'pi_id': 1, 'research_direction_score': 50.0, 'mentorship_style_score': 58.0, 'funding_stability_score': 90.0, 'culture_fit_score': 60.0, 'technical_skills_score': 60.0, 'location_score': 100.0, 'is_direct_connection': False, 'is_indirect_connection': True, 'indirect_conn
