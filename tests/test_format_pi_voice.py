#!/usr/bin/env python3
"""
tests/test_format_pi_voice.py

Standalone test for Issue 1: verifies that _format_pi_voice() correctly
extracts and renders autonomy_style, intervention_level, work_life_balance,
meeting_frequency, and funding_note from Lior Pachter's seed data.

Does not modify any existing file. Run with:
    python3 tests/test_format_pi_voice.py
"""

import json
import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.pi_avatar import _format_pi_voice

SEED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "seeds", "caltech_pis.json",
)

# ── Load Pachter's pi_survey ──────────────────────────────────────────────────
with open(SEED_PATH, encoding="utf-8") as f:
    pis = json.load(f)

pachter = next((p for p in pis if "Pachter" in p["name"]), None)
assert pachter is not None, "Lior Pachter not found in caltech_pis.json"

pi_survey = pachter["pi_survey"]

print("=" * 60)
print(f"PI: {pachter['name']}")
print(f"pi_survey keys: {list(pi_survey.keys())}")
print("=" * 60)
print()

# ── Call _format_pi_voice directly ───────────────────────────────────────────
output = _format_pi_voice(pi_survey)
print("_format_pi_voice output:")
print(output)
print()

# ── Assertions ────────────────────────────────────────────────────────────────
CHECKS = {
    "autonomy_style":      "Independence expectation:",
    "intervention_level":  "PI involvement level:",
    "work_life_balance":   "Work-life balance stance:",
    "meeting_frequency":   "meetings",        # embedded in Mentorship style line
    "funding_note":        "Funding note:",
}

print("=" * 60)
print("Checks:")
all_passed = True
for field, marker in CHECKS.items():
    found = marker.lower() in output.lower()
    status = "PASS" if found else "FAIL"
    if not found:
        all_passed = False
    print(f"  [{status}] {field!r} → expected marker {marker!r}")

print()
if all_passed:
    print("ALL CHECKS PASSED")
else:
    print("ONE OR MORE CHECKS FAILED")
    sys.exit(1)
