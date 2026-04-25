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

from database import create_db_and_tables, engine  # noqa: E402
from routers import pi, simulation, survey          # noqa: E402


def _auto_seed_pis():
    """Seed Caltech PIs on first startup if the table is empty."""
    from sqlmodel import Session, select
    from models import PIProfile
    from schemas import PIProfileSeedItem

    seed_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "seeds", "caltech_pis.json")
    )
    if not os.path.exists(seed_path):
        return

    with Session(engine) as session:
        if session.exec(select(PIProfile)).first():
            return  # already seeded
        with open(seed_path, encoding="utf-8") as f:
            entries = json.load(f)
        for entry in entries:
            item = PIProfileSeedItem(**entry)
            session.add(PIProfile(**item.model_dump()))
        session.commit()
        print(f"[startup] Seeded {len(entries)} PIs from {seed_path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    _auto_seed_pis()
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
    return {"status": "ok"}
