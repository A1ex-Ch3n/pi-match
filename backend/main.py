import json
import logging
import os
import re
import sys
from contextlib import asynccontextmanager

# Configure pimatch logger to appear alongside uvicorn output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("pimatch.matching").setLevel(logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path so `agents` package is importable
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.database import create_db_and_tables, engine  # noqa: E402
from backend.routers import pi, simulation, survey          # noqa: E402


def _auto_seed_pis():
    """Seed PIs from all_pis_east.json, all_pis_west.json (project root) and
    all *_pis.json files in data/seeds/.

    Additive: skips any PI whose name is already in the table, so new seed
    files can be added without requiring a DB reset.
    """
    from sqlmodel import Session, select
    from backend.models import PIProfile
    from backend.schemas import PIProfileSeedItem
    from data.adapters import load_and_adapt_file

    seeds_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "seeds")
    )

    seed_files = sorted(
        f for f in os.listdir(seeds_dir)
        if f.endswith("_pis.json")
    ) if os.path.isdir(seeds_dir) else []

    from data.dedup_seeds import dedup_entries

    # Collect entries: root-level east/west files first, then existing seeds
    raw: list = []

    for filename in ("all_pis_east.json", "all_pis_west.json"):
        path = os.path.join(_PROJECT_ROOT, filename)
        if os.path.exists(path):
            adapted = load_and_adapt_file(path)
            raw.extend(adapted)
            print(f"[startup] Adapted {len(adapted)} PIs from {filename}")

    for filename in seed_files:
        path = os.path.join(seeds_dir, filename)
        with open(path, encoding="utf-8") as f:
            raw.extend(json.load(f))

    if not raw:
        return

    clean = dedup_entries(raw)

    with Session(engine) as session:
        existing_count = session.exec(select(PIProfile)).all()
        if len(existing_count) >= len(clean):
            print(f"[startup] DB already has {len(existing_count)} PI(s) — skipping seed.")
            return

        total = 0
        skipped = 0
        for entry in clean:
            name = entry["name"]
            existing = session.exec(
                select(PIProfile).where(PIProfile.name == name)
            ).first()
            if existing:
                print(f"[startup] Skipping '{name}' — already in database (id={existing.id})")
                skipped += 1
                continue
            try:
                item = PIProfileSeedItem(**entry)
                session.add(PIProfile(**item.model_dump()))
                total += 1
            except Exception as exc:
                print(f"[startup] Error seeding '{name}': {exc}")
        if total:
            session.commit()
            print(f"[startup] Seeded {total} new PI(s) ({skipped} duplicate(s) skipped)")


def _dedup_db_pis():
    """Merge duplicate PI rows that the name-based dedup missed.

    Catches two cases:
      1. Same personal lab_website where the PI's last name appears in the URL
         (e.g. Patricia Wittkopp / Trisha Wittkopp sharing the same faculty page).
      2. Same email address under different name spellings.

    For each duplicate pair, keeps the richer record and deletes the other.
    MatchResult rows for the deleted PI are also removed (they'll be regenerated
    on the next match run).
    """
    from sqlmodel import Session, select
    from sqlalchemy import text as sa_text
    from backend.models import PIProfile, MatchResult
    import re

    def _norm_url(url: str) -> str:
        url = (url or "").lower().strip().rstrip("/")
        return re.sub(r"^https?://(www\.)?", "", url)

    def _richness(pi: PIProfile) -> int:
        score = 0
        score += len(pi.research_areas or []) * 3
        score += len(pi.recent_abstracts or []) * 2
        score += len(pi.papers or []) * 2
        score += bool(pi.pi_survey) * 5
        score += len(pi.student_survey_responses or []) * 4
        score += bool(pi.institution and pi.institution.lower() not in ("unknown", "")) * 4
        return score

    def _name_key(name: str) -> str:
        name = name.split("/")[0].strip()
        return re.sub(r"\s+", " ", name).lower().strip()

    with Session(engine) as session:
        all_pis = session.exec(select(PIProfile)).all()
        to_delete: set[int] = set()
        merged_count = 0

        for i, pi_a in enumerate(all_pis):
            if pi_a.id in to_delete:
                continue
            url_a = _norm_url(pi_a.lab_website)
            last_a = (_name_key(pi_a.name).split() or [""])[-1]

            for pi_b in all_pis[i + 1:]:
                if pi_b.id in to_delete:
                    continue
                is_dup = False

                # Same personal URL (last name must appear in URL)
                url_b = _norm_url(pi_b.lab_website)
                if url_a and url_b and url_a == url_b:
                    last_b = (_name_key(pi_b.name).split() or [""])[-1]
                    if (last_a and last_a in url_a) or (last_b and last_b in url_b):
                        is_dup = True

                # Same non-empty email
                if not is_dup:
                    ea = (pi_a.email or "").lower().strip()
                    eb = (pi_b.email or "").lower().strip()
                    if ea and eb and ea == eb:
                        is_dup = True

                if is_dup:
                    keep, drop = (pi_a, pi_b) if _richness(pi_a) >= _richness(pi_b) else (pi_b, pi_a)
                    print(f"[startup] Dedup: '{keep.name}' keeps, '{drop.name}' removed")
                    to_delete.add(drop.id)
                    merged_count += 1

        if to_delete:
            for pid in to_delete:
                # Remove dependent MatchResult rows first
                matches = session.exec(select(MatchResult).where(MatchResult.pi_id == pid)).all()
                for m in matches:
                    session.delete(m)
                pi_obj = session.get(PIProfile, pid)
                if pi_obj:
                    session.delete(pi_obj)
            session.commit()
            print(f"[startup] Removed {merged_count} duplicate PI record(s)")


def _run_migrations():
    """Apply lightweight schema migrations that create_db_and_tables() won't handle
    (SQLAlchemy never ALTERs existing tables, only creates missing ones)."""
    from sqlalchemy import text as sa_text
    with engine.connect() as conn:
        # Add field_category column to studentprofile if not present
        existing = {row[1] for row in conn.execute(sa_text("PRAGMA table_info(studentprofile)"))}
        if "field_category" not in existing:
            conn.execute(sa_text("ALTER TABLE studentprofile ADD COLUMN field_category TEXT DEFAULT 'any'"))
            print("[startup] Migration: added field_category to studentprofile")

        # Enforce uniqueness on PI names — prevents duplicate rows from future seeds
        conn.execute(sa_text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_piprofile_name ON piprofile(name)"
        ))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    _run_migrations()
    _dedup_db_pis()
    _auto_seed_pis()
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        print("WARNING: ANTHROPIC_API_KEY is not set. All Claude calls will return mock responses.")
    yield


app = FastAPI(
    title="PiMatch API",
    version="1.0.0",
    description="PhD advisor matchmaking platform",
    lifespan=lifespan,
)

# Allow any origin in production — lock down to specific domains post-MVP
_allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(survey.router, prefix="/api")
app.include_router(pi.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "PiMatch API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_configured": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
    }
