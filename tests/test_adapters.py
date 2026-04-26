#!/usr/bin/env python3
"""
tests/test_adapters.py

Unit tests for data/adapters.py — no server or database required.
Run with: python3 tests/test_adapters.py
"""
import sys
import os
import datetime
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.adapters import adapt_east_pi, adapt_west_pi, detect_format, load_and_adapt_file

CURRENT_YEAR = datetime.date.today().year
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EAST_SAMPLE = {
    "school_slug": "harvard_csb",
    "name": "Jane Doe",
    "school": "Harvard University",
    "department": "Computer Science",
    "email": "jdoe@harvard.edu",
    "url": "https://jdoe.seas.harvard.edu/",
    "research_areas": ["machine learning", "genomics"],
    "semantic_scholar_id": "123456",
    "h_index": 30,
    "citation_count": 5000,
    "recent_top_papers": [
        {"title": "Old Paper", "year": 2021, "citations": 50},
        {"title": "New Paper", "year": CURRENT_YEAR, "citations": 5},
    ],
    "funding_agencies": ["NIH"],
    "total_active_funding_usd": 1000000,
    "recruiting_status": {"tier": -1, "notes": "dry-run — not assessed"},
}

WEST_SAMPLE = {
    "region": "ca",
    "school_slug": "caltech",
    "name": "John Smith",
    "institution": "Caltech",
    "campus_slug": None,
    "department": "Biology",
    "department_slug": None,
    "email": "jsmith@caltech.edu",
    "lab_website": "https://jsmith.caltech.edu/",
    "tier": 1,
    "location": "CA",
    "lab_size": 10,
    "is_recruiting": True,
    "recruiting_status": {
        "status": "actively_recruiting",
        "tier": 1,
        "score": 0.9,
        "signals": {},
        "rationale": "",
    },
    "recruiting_last_verified": None,
    "mentorship_modes": [],
    "source_url": None,
    "source_notes": None,
    "research_areas": ["protein folding", "structural biology"],
    "recent_papers": [
        {
            "doi": "10.1/x",
            "title": "Protein Paper",
            "year": 2023,
            "publication_date": "2023-01",
            "venue": "Nature",
            "abstract": "A paper about proteins.",
            "external_ids": {},
        }
    ],
    "recent_abstracts": ["A paper about proteins."],
    "funding_sources": [],
    "funding_agencies": ["NIH"],
    "total_active_funding_usd": 500000,
    "funding_citizen_restricted": False,
    "nsf_grants": [],
    "has_active_nsf_grant": False,
    "semantic_scholar_id": "789012",
    "co_author_ids": ["111", "222"],
    "papers_last_12_months": 2,
    "reply_likelihood": "High",
    "pi_survey": None,
    "student_survey_responses": [],
}


class TestAdaptEastPi(unittest.TestCase):
    def setUp(self):
        self.adapted = adapt_east_pi(EAST_SAMPLE)

    def test_institution_mapped_from_school(self):
        self.assertEqual(self.adapted["institution"], "Harvard University")

    def test_lab_website_mapped_from_url(self):
        self.assertEqual(self.adapted["lab_website"], "https://jdoe.seas.harvard.edu/")

    def test_recent_top_papers_mapped_to_papers(self):
        papers = self.adapted["papers"]
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0]["title"], "Old Paper")
        self.assertIn("year", papers[0])
        self.assertIn("citations", papers[0])

    def test_location_harvard_is_ma(self):
        self.assertEqual(self.adapted["location"], "MA")

    def test_location_cornell_is_ny(self):
        raw = {**EAST_SAMPLE, "school": "Cornell University"}
        self.assertEqual(adapt_east_pi(raw)["location"], "NY")

    def test_location_brown_is_ri(self):
        raw = {**EAST_SAMPLE, "school": "Brown University"}
        self.assertEqual(adapt_east_pi(raw)["location"], "RI")

    def test_location_dartmouth_is_nh(self):
        raw = {**EAST_SAMPLE, "school": "Dartmouth College"}
        self.assertEqual(adapt_east_pi(raw)["location"], "NH")

    def test_location_mit_is_ma(self):
        raw = {**EAST_SAMPLE, "school": "MIT"}
        self.assertEqual(adapt_east_pi(raw)["location"], "MA")

    def test_dry_run_tier_defaults_to_2(self):
        self.assertEqual(self.adapted["tier"], 2)

    def test_non_dry_run_tier_preserved(self):
        raw = {**EAST_SAMPLE, "recruiting_status": {"tier": 1, "notes": ""}}
        self.assertEqual(adapt_east_pi(raw)["tier"], 1)

    def test_is_recruiting_defaults_true(self):
        self.assertTrue(self.adapted["is_recruiting"])

    def test_papers_last_12_months_counts_recent(self):
        self.assertEqual(self.adapted["papers_last_12_months"], 1)

    def test_default_co_author_ids_empty(self):
        self.assertEqual(self.adapted["co_author_ids"], [])

    def test_default_co_author_names_empty(self):
        self.assertEqual(self.adapted["co_author_names"], [])

    def test_default_nsf_grants_empty(self):
        self.assertEqual(self.adapted["nsf_grants"], [])

    def test_default_has_active_nsf_grant_false(self):
        self.assertFalse(self.adapted["has_active_nsf_grant"])

    def test_default_funding_citizen_restricted_false(self):
        self.assertFalse(self.adapted["funding_citizen_restricted"])

    def test_recent_abstracts_empty(self):
        self.assertEqual(self.adapted["recent_abstracts"], [])

    def test_default_lab_size_5(self):
        self.assertEqual(self.adapted["lab_size"], 5)

    def test_default_reply_likelihood_medium(self):
        self.assertEqual(self.adapted["reply_likelihood"], "medium")

    def test_default_pi_survey_none(self):
        self.assertIsNone(self.adapted["pi_survey"])

    def test_default_student_survey_responses_empty(self):
        self.assertEqual(self.adapted["student_survey_responses"], [])

    def test_extra_fields_dropped(self):
        for key in ("h_index", "citation_count", "school_slug", "funding_agencies", "school", "url"):
            self.assertNotIn(key, self.adapted, f"Extra field '{key}' should not be in output")

    def test_unknown_school_location_empty_string(self):
        raw = {**EAST_SAMPLE, "school": "Unknown Ivy"}
        self.assertEqual(adapt_east_pi(raw)["location"], "")

    def test_schema_compatible(self):
        from backend.schemas import PIProfileSeedItem
        item = PIProfileSeedItem(**self.adapted)
        self.assertEqual(item.name, "Jane Doe")


class TestAdaptWestPi(unittest.TestCase):
    def setUp(self):
        self.adapted = adapt_west_pi(WEST_SAMPLE)

    def test_reply_likelihood_high_lowercased(self):
        self.assertEqual(self.adapted["reply_likelihood"], "high")

    def test_reply_likelihood_medium_lowercased(self):
        raw = {**WEST_SAMPLE, "reply_likelihood": "Medium"}
        self.assertEqual(adapt_west_pi(raw)["reply_likelihood"], "medium")

    def test_reply_likelihood_low_lowercased(self):
        raw = {**WEST_SAMPLE, "reply_likelihood": "Low"}
        self.assertEqual(adapt_west_pi(raw)["reply_likelihood"], "low")

    def test_reply_likelihood_none_preserved(self):
        raw = {**WEST_SAMPLE, "reply_likelihood": None}
        self.assertIsNone(adapt_west_pi(raw)["reply_likelihood"])

    def test_recent_papers_mapped_to_papers(self):
        papers = self.adapted["papers"]
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["title"], "Protein Paper")
        self.assertEqual(papers[0]["year"], 2023)

    def test_papers_extra_fields_dropped(self):
        paper = self.adapted["papers"][0]
        for key in ("doi", "publication_date", "venue", "abstract", "external_ids"):
            self.assertNotIn(key, paper, f"Paper field '{key}' should be dropped")

    def test_pi_survey_all_null_normalized_to_none(self):
        raw = {**WEST_SAMPLE, "pi_survey": {"f1": None, "f2": None, "f3": None}}
        self.assertIsNone(adapt_west_pi(raw)["pi_survey"])

    def test_pi_survey_with_real_data_preserved(self):
        raw = {**WEST_SAMPLE, "pi_survey": {"mentorship_style": "hands-on", "meeting_frequency": None}}
        result = adapt_west_pi(raw)
        self.assertIsNotNone(result["pi_survey"])
        self.assertEqual(result["pi_survey"]["mentorship_style"], "hands-on")

    def test_co_author_names_defaults_to_empty(self):
        self.assertEqual(self.adapted["co_author_names"], [])

    def test_tier_uses_top_level_not_rs_tier(self):
        raw = {**WEST_SAMPLE, "tier": 3}
        self.assertEqual(adapt_west_pi(raw)["tier"], 3)

    def test_is_recruiting_top_level_false_wins(self):
        raw = {**WEST_SAMPLE, "is_recruiting": False}
        self.assertFalse(adapt_west_pi(raw)["is_recruiting"])

    def test_is_recruiting_derived_actively_recruiting(self):
        raw = {**WEST_SAMPLE, "is_recruiting": None,
               "recruiting_status": {"status": "actively_recruiting"}}
        self.assertTrue(adapt_west_pi(raw)["is_recruiting"])

    def test_is_recruiting_derived_not_seeking(self):
        raw = {**WEST_SAMPLE, "is_recruiting": None,
               "recruiting_status": {"status": "not_seeking"}}
        self.assertFalse(adapt_west_pi(raw)["is_recruiting"])

    def test_is_recruiting_derived_unknown_status_defaults_true(self):
        raw = {**WEST_SAMPLE, "is_recruiting": None,
               "recruiting_status": {"status": "something_else"}}
        self.assertTrue(adapt_west_pi(raw)["is_recruiting"])

    def test_extra_fields_dropped(self):
        extra = (
            "region", "school_slug", "campus_slug", "department_slug",
            "mentorship_modes", "source_url", "source_notes",
            "funding_sources", "recruiting_last_verified", "recruiting_status",
        )
        for key in extra:
            self.assertNotIn(key, self.adapted, f"Extra field '{key}' should not be in output")

    def test_schema_compatible(self):
        from backend.schemas import PIProfileSeedItem
        item = PIProfileSeedItem(**self.adapted)
        self.assertEqual(item.name, "John Smith")


class TestDetectFormat(unittest.TestCase):
    def test_east_record_has_school_and_url(self):
        self.assertEqual(detect_format({"school": "MIT", "url": "http://x.edu"}), "east")

    def test_west_record_has_institution_and_region(self):
        self.assertEqual(detect_format({"institution": "Caltech", "region": "ca"}), "west")

    def test_west_record_institution_only(self):
        self.assertEqual(detect_format({"institution": "Caltech"}), "west")

    def test_west_record_region_only(self):
        self.assertEqual(detect_format({"region": "ca"}), "west")

    def test_ambiguous_record_raises(self):
        with self.assertRaises(ValueError):
            detect_format({"foo": "bar", "baz": "qux"})


class TestLoadAndAdaptFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.east_path = os.path.join(_ROOT, "all_pis_east.json")
        cls.west_path = os.path.join(_ROOT, "all_pis_west.json")
        cls.east = load_and_adapt_file(cls.east_path) if os.path.exists(cls.east_path) else None
        cls.west = load_and_adapt_file(cls.west_path) if os.path.exists(cls.west_path) else None

    def test_east_file_produces_83_records(self):
        if self.east is None:
            self.skipTest("all_pis_east.json not found")
        self.assertEqual(len(self.east), 83)

    def test_west_file_produces_1117_records(self):
        if self.west is None:
            self.skipTest("all_pis_west.json not found")
        self.assertEqual(len(self.west), 1117)

    def test_east_all_records_schema_valid(self):
        if self.east is None:
            self.skipTest("all_pis_east.json not found")
        from backend.schemas import PIProfileSeedItem
        for item in self.east:
            PIProfileSeedItem(**item)

    def test_west_all_records_schema_valid(self):
        if self.west is None:
            self.skipTest("all_pis_west.json not found")
        from backend.schemas import PIProfileSeedItem
        for item in self.west:
            PIProfileSeedItem(**item)

    def test_west_reply_likelihood_all_lowercase(self):
        if self.west is None:
            self.skipTest("all_pis_west.json not found")
        for item in self.west:
            rl = item.get("reply_likelihood")
            if rl is not None:
                self.assertEqual(rl, rl.lower(),
                                 f"Not lowercase: {rl!r} for {item['name']}")

    def test_east_locations_valid_state_codes(self):
        if self.east is None:
            self.skipTest("all_pis_east.json not found")
        valid = {"RI", "NY", "NH", "MA", "NJ", "PA", "CT", ""}
        for item in self.east:
            self.assertIn(item["location"], valid,
                          f"Invalid location {item['location']!r} for {item['name']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
