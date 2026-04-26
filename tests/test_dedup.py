#!/usr/bin/env python3
"""
tests/test_dedup.py

Tests dedup_entries() correctly merges east + west + caltech seed data.
No live server or database required.
Run with: python3 tests/test_dedup.py
"""
import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dedup_seeds import dedup_entries
from data.adapters import load_and_adapt_file

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_caltech():
    path = os.path.join(_ROOT, "data", "seeds", "caltech_pis.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestDedupCombined(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        east_path = os.path.join(_ROOT, "all_pis_east.json")
        west_path = os.path.join(_ROOT, "all_pis_west.json")

        cls.east = load_and_adapt_file(east_path) if os.path.exists(east_path) else []
        cls.west = load_and_adapt_file(west_path) if os.path.exists(west_path) else []
        cls.caltech = _load_caltech()

        cls.combined_raw = cls.east + cls.west + cls.caltech
        cls.deduped = dedup_entries(cls.combined_raw)
        cls.deduped_names_lower = [e["name"].lower() for e in cls.deduped]

    def _skip_if_missing(self, *sources):
        missing = [s for s in sources if not getattr(self, s)]
        if missing:
            self.skipTest(f"Source file(s) not found: {missing}")

    def test_no_duplicate_names_after_dedup(self):
        seen = set()
        for name in self.deduped_names_lower:
            self.assertNotIn(name, seen, f"Duplicate name: {name!r}")
            seen.add(name)

    def test_deduped_count_less_than_raw_sum(self):
        self._skip_if_missing("east", "west", "caltech")
        self.assertLess(len(self.deduped), len(self.combined_raw))

    def test_caltech_pis_all_present_after_dedup(self):
        self._skip_if_missing("caltech")
        for entry in self.caltech:
            name = entry.get("name", "")
            if not name:
                continue
            found = any(name.lower() in n for n in self.deduped_names_lower)
            self.assertTrue(found, f"Caltech PI {name!r} missing from deduped result")

    def test_unknown_names_dropped(self):
        sentinel = {"name": "Unknown", "institution": "X", "department": "Y"}
        raw = list(self.combined_raw) + [sentinel]
        result = dedup_entries(raw)
        self.assertNotIn("unknown", [e["name"].lower() for e in result])

    def test_no_east_west_overlap(self):
        self._skip_if_missing("east", "west")
        east_names = {e["name"].lower() for e in self.east}
        west_names = {e["name"].lower() for e in self.west}
        overlap = east_names & west_names
        self.assertEqual(len(overlap), 0, f"Unexpected east/west overlap: {overlap}")

    def test_caltech_abstracts_win_over_west(self):
        """Caltech entry (with abstracts) should beat west entry (no abstracts) for Pachter."""
        self._skip_if_missing("caltech")
        caltech_pachter = next(
            (e for e in self.caltech if "Pachter" in e.get("name", "")), None
        )
        if caltech_pachter is None:
            self.skipTest("Pachter not in caltech_pis.json")
        if not caltech_pachter.get("recent_abstracts"):
            self.skipTest("Caltech Pachter has no abstracts to test with")

        deduped_pachter = next(
            (e for e in self.deduped if "Pachter" in e.get("name", "")), None
        )
        self.assertIsNotNone(deduped_pachter, "Pachter not found in deduped results")
        self.assertTrue(
            len(deduped_pachter.get("recent_abstracts") or []) > 0,
            "Pachter's abstracts should be preserved after dedup (caltech entry should win)",
        )

    def test_total_count_expected_range(self):
        """After merging east(83) + west(1117) + caltech(~5) with ~5 overlaps, expect ~1200."""
        self._skip_if_missing("east", "west", "caltech")
        self.assertGreater(len(self.deduped), 1100)
        self.assertLess(len(self.deduped), len(self.combined_raw))


class TestDedupUnit(unittest.TestCase):
    """Fast unit tests that don't require the large source files."""

    def test_two_identical_names_merged_to_one(self):
        entries = [
            {"name": "Alice Smith", "institution": "MIT", "department": "CS",
             "research_areas": ["ML"], "recent_abstracts": ["Abstract 1"]},
            {"name": "Alice Smith", "institution": "MIT", "department": "CS",
             "research_areas": ["NLP"], "recent_abstracts": []},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 1)

    def test_richer_entry_wins_on_research_areas(self):
        entries = [
            {"name": "Bob Jones", "institution": "Harvard", "department": "Bio",
             "research_areas": [], "recent_abstracts": []},
            {"name": "Bob Jones", "institution": "Harvard", "department": "Bio",
             "research_areas": ["genomics", "evolution"], "recent_abstracts": ["Abstract A"]},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 1)
        self.assertIn("genomics", result[0].get("research_areas", []))

    def test_blank_name_dropped(self):
        entries = [
            {"name": "", "institution": "X", "department": "Y"},
            {"name": "Valid Person", "institution": "MIT", "department": "CS",
             "research_areas": []},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Valid Person")

    def test_different_names_kept_separate(self):
        entries = [
            {"name": "Alice Smith", "institution": "MIT", "department": "CS",
             "research_areas": []},
            {"name": "Bob Jones", "institution": "Harvard", "department": "Bio",
             "research_areas": []},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 2)

    def test_unknown_pi_dropped(self):
        entries = [
            {"name": "Unknown PI", "institution": "X", "department": "Y"},
            {"name": "Real Person", "institution": "MIT", "department": "CS",
             "research_areas": []},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Real Person")

    def test_merge_preserves_richer_fields(self):
        """Primary (richer) entry's non-empty fields overwrite secondary's."""
        entries = [
            {"name": "Carol Kim", "institution": "Caltech", "department": "Physics",
             "research_areas": ["quantum", "photonics"],
             "recent_abstracts": ["Photon abstract"],
             "pi_survey": {"mentorship_style": "hands-on"},
             "student_survey_responses": [{"overall_experience": "great"}]},
            {"name": "Carol Kim", "institution": "Caltech", "department": "Physics",
             "research_areas": [],
             "recent_abstracts": [],
             "pi_survey": None,
             "student_survey_responses": []},
        ]
        result = dedup_entries(entries)
        self.assertEqual(len(result), 1)
        self.assertIn("quantum", result[0]["research_areas"])
        self.assertTrue(result[0]["recent_abstracts"])
        self.assertIsNotNone(result[0]["pi_survey"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
