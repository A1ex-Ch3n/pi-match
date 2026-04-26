#!/usr/bin/env python3
"""
tests/test_seeding.py

Integration tests: seed adapted east/west PIs into a temporary in-memory SQLite
database and verify DB records. No live server required.
Run with: python3 tests/test_seeding.py
"""
import sys
import os
import datetime
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlmodel import Session, create_engine, SQLModel, select
from backend.models import PIProfile
from backend.schemas import PIProfileSeedItem
from data.adapters import adapt_east_pi, adapt_west_pi, load_and_adapt_file

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CURRENT_YEAR = datetime.date.today().year

EAST_BATCH = [
    {
        "school_slug": "harvard_csb",
        "name": "Alice Researcher",
        "school": "Harvard University",
        "department": "Computer Science",
        "email": "alice@harvard.edu",
        "url": "https://alice.seas.harvard.edu/",
        "research_areas": ["ML", "genomics"],
        "semantic_scholar_id": "001",
        "h_index": 10,
        "citation_count": 500,
        "recent_top_papers": [{"title": "Paper A", "year": _CURRENT_YEAR, "citations": 5}],
        "funding_agencies": ["NIH"],
        "total_active_funding_usd": 100000,
        "recruiting_status": {"tier": -1, "notes": "dry-run"},
    },
    {
        "school_slug": "cornell_csb",
        "name": "Bob Scientist",
        "school": "Cornell University",
        "department": "Biology",
        "email": "bob@cornell.edu",
        "url": "https://bob.cs.cornell.edu/",
        "research_areas": ["bioinformatics"],
        "semantic_scholar_id": "002",
        "h_index": 5,
        "citation_count": 200,
        "recent_top_papers": [],
        "funding_agencies": [],
        "total_active_funding_usd": None,
        "recruiting_status": {"tier": -1, "notes": "dry-run"},
    },
    {
        "school_slug": "mit_csb",
        "name": "Carol Engineer",
        "school": "MIT",
        "department": "EECS",
        "email": None,
        "url": None,
        "research_areas": ["algorithms", "theory"],
        "semantic_scholar_id": "003",
        "h_index": 20,
        "citation_count": 2000,
        "recent_top_papers": [],
        "funding_agencies": ["NSF"],
        "total_active_funding_usd": 200000,
        "recruiting_status": {"tier": 1, "notes": ""},
    },
]

WEST_BATCH = [
    {
        "region": "ca",
        "school_slug": "caltech",
        "name": "Dave Professor",
        "institution": "Caltech",
        "campus_slug": None,
        "department": "Physics",
        "department_slug": None,
        "email": "dave@caltech.edu",
        "lab_website": "https://dave.caltech.edu/",
        "tier": 1,
        "location": "CA",
        "lab_size": 8,
        "is_recruiting": True,
        "recruiting_status": {"status": "actively_recruiting", "tier": 1, "score": 0.9, "signals": {}, "rationale": ""},
        "recruiting_last_verified": None,
        "mentorship_modes": [],
        "source_url": None,
        "source_notes": None,
        "research_areas": ["quantum computing"],
        "recent_papers": [
            {"doi": "10.x", "title": "Quantum Paper", "year": 2023,
             "publication_date": "2023-01", "venue": "PRL",
             "abstract": "Quantum.", "external_ids": {}}
        ],
        "recent_abstracts": ["Quantum."],
        "funding_sources": [],
        "funding_agencies": ["NSF"],
        "total_active_funding_usd": 300000,
        "funding_citizen_restricted": False,
        "nsf_grants": [],
        "has_active_nsf_grant": False,
        "semantic_scholar_id": "004",
        "co_author_ids": ["555"],
        "papers_last_12_months": 1,
        "reply_likelihood": "Medium",
        "pi_survey": None,
        "student_survey_responses": [],
    },
    {
        "region": "ca",
        "school_slug": "ucsb",
        "name": "Eve Biologist",
        "institution": "UC Santa Barbara",
        "campus_slug": None,
        "department": "Biology",
        "department_slug": None,
        "email": "eve@ucsb.edu",
        "lab_website": None,
        "tier": 2,
        "location": "CA",
        "lab_size": 4,
        "is_recruiting": None,
        "recruiting_status": {
            "status": "not_seeking",
            "tier": 0,
            "score": 0.1,
            "signals": {},
            "rationale": "",
        },
        "recruiting_last_verified": None,
        "mentorship_modes": [],
        "source_url": None,
        "source_notes": None,
        "research_areas": ["ecology"],
        "recent_papers": [],
        "recent_abstracts": [],
        "funding_sources": [],
        "funding_agencies": [],
        "total_active_funding_usd": None,
        "funding_citizen_restricted": False,
        "nsf_grants": [],
        "has_active_nsf_grant": False,
        "semantic_scholar_id": None,
        "co_author_ids": [],
        "papers_last_12_months": 0,
        "reply_likelihood": None,
        "pi_survey": {"research_philosophy": None, "what_i_look_for": None},
        "student_survey_responses": [],
    },
]


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


class TestEastBatchSeeding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = _make_engine()
        adapted = [adapt_east_pi(r) for r in EAST_BATCH]
        with Session(cls.engine) as session:
            for entry in adapted:
                item = PIProfileSeedItem(**entry)
                session.add(PIProfile(**item.model_dump()))
            session.commit()

    def _get(self, name):
        with Session(self.engine) as session:
            return session.exec(select(PIProfile).where(PIProfile.name == name)).first()

    def test_three_records_inserted(self):
        with Session(self.engine) as session:
            count = len(session.exec(select(PIProfile)).all())
        self.assertEqual(count, 3)

    def test_institution_mapped_from_school(self):
        self.assertEqual(self._get("Alice Researcher").institution, "Harvard University")

    def test_location_harvard_is_ma(self):
        self.assertEqual(self._get("Alice Researcher").location, "MA")

    def test_location_cornell_is_ny(self):
        self.assertEqual(self._get("Bob Scientist").location, "NY")

    def test_location_mit_is_ma(self):
        self.assertEqual(self._get("Carol Engineer").location, "MA")

    def test_non_dry_run_tier_preserved(self):
        self.assertEqual(self._get("Carol Engineer").tier, 1)

    def test_dry_run_tier_defaults_to_2(self):
        self.assertEqual(self._get("Alice Researcher").tier, 2)

    def test_papers_last_12_months_counted(self):
        self.assertEqual(self._get("Alice Researcher").papers_last_12_months, 1)


class TestWestBatchSeeding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = _make_engine()
        adapted = [adapt_west_pi(r) for r in WEST_BATCH]
        with Session(cls.engine) as session:
            for entry in adapted:
                item = PIProfileSeedItem(**entry)
                session.add(PIProfile(**item.model_dump()))
            session.commit()

    def _get(self, name):
        with Session(self.engine) as session:
            return session.exec(select(PIProfile).where(PIProfile.name == name)).first()

    def test_reply_likelihood_normalized_to_lowercase(self):
        self.assertEqual(self._get("Dave Professor").reply_likelihood, "medium")

    def test_papers_mapped_from_recent_papers(self):
        import json as _json
        dave = self._get("Dave Professor")
        papers = dave.papers
        if isinstance(papers, str):
            papers = _json.loads(papers)
        self.assertIsNotNone(papers)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["title"], "Quantum Paper")

    def test_pi_survey_all_null_stored_as_none(self):
        self.assertIsNone(self._get("Eve Biologist").pi_survey)

    def test_is_recruiting_derived_not_seeking(self):
        self.assertFalse(self._get("Eve Biologist").is_recruiting)

    def test_co_author_names_empty_list(self):
        dave = self._get("Dave Professor")
        self.assertFalse(dave.co_author_names)


class TestIdempotency(unittest.TestCase):
    def test_seed_same_record_twice_no_duplicates(self):
        engine = _make_engine()
        entry = adapt_east_pi(EAST_BATCH[0])

        def seed(session, entries):
            count = 0
            for e in entries:
                existing = session.exec(
                    select(PIProfile).where(PIProfile.name == e["name"])
                ).first()
                if not existing:
                    item = PIProfileSeedItem(**e)
                    session.add(PIProfile(**item.model_dump()))
                    count += 1
            session.commit()
            return count

        with Session(engine) as s:
            first = seed(s, [entry])
        with Session(engine) as s:
            second = seed(s, [entry])
        with Session(engine) as s:
            total = len(s.exec(select(PIProfile)).all())

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(total, 1)

    def test_seed_count_with_fresh_session(self):
        engine = _make_engine()
        entry = adapt_east_pi(EAST_BATCH[0])
        with Session(engine) as s:
            item = PIProfileSeedItem(**entry)
            s.add(PIProfile(**item.model_dump()))
            s.commit()
        with Session(engine) as s:
            count = len(s.exec(select(PIProfile)).all())
        self.assertEqual(count, 1)


class TestFullFileSchemaValidation(unittest.TestCase):
    def test_east_full_file_schema_valid(self):
        path = os.path.join(_ROOT, "all_pis_east.json")
        if not os.path.exists(path):
            self.skipTest("all_pis_east.json not found")
        for entry in load_and_adapt_file(path):
            PIProfileSeedItem(**entry)

    def test_west_full_file_schema_valid(self):
        path = os.path.join(_ROOT, "all_pis_west.json")
        if not os.path.exists(path):
            self.skipTest("all_pis_west.json not found")
        for entry in load_and_adapt_file(path):
            PIProfileSeedItem(**entry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
