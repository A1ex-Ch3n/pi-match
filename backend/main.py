import json
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path so `agents` package is importable
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.database import create_db_and_tables, engine  # noqa: E402
from backend.routers import pi, simulation, survey          # noqa: E402


def _auto_seed_pis():
    """Seed PIs from all *_pis.json files in data/seeds/.

    Additive: skips any PI whose name is already in the table, so new seed
    files can be added without requiring a DB reset.
    """
    from sqlmodel import Session, select
    from backend.models import PIProfile
    from backend.schemas import PIProfileSeedItem

    seeds_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "seeds")
    )

    seed_files = sorted(
        f for f in os.listdir(seeds_dir)
        if f.endswith("_pis.json")
    ) if os.path.isdir(seeds_dir) else []

    if not seed_files:
        return

    from data.dedup_seeds import dedup_entries

    # Collect all entries across every seed file, then dedup/merge before touching the DB
    raw: list = []
    for filename in seed_files:
        path = os.path.join(seeds_dir, filename)
        with open(path, encoding="utf-8") as f:
            raw.extend(json.load(f))

    clean = dedup_entries(raw)

    with Session(engine) as session:
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
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
