import json
import os
import sys
from typing import List, Optional

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import PIProfile
from backend.schemas import PIProfileResponse, PIProfileSeedItem, SeedRequest

router = APIRouter()

_DEFAULT_SEED = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "seeds", "caltech_pis.json"
)


@router.get("/pi/list", response_model=List[PIProfileResponse])
def list_pis(session: Session = Depends(get_session)):
    return session.exec(select(PIProfile)).all()


@router.get("/pi/{pi_id}", response_model=PIProfileResponse)
def get_pi(pi_id: int, session: Session = Depends(get_session)):
    pi = session.get(PIProfile, pi_id)
    if not pi:
        raise HTTPException(status_code=404, detail="PI not found")
    return pi


@router.post("/pi/seed")
def seed_pis(
    session: Session = Depends(get_session),
    request: Optional[SeedRequest] = Body(default=None),
):
    file_path = (request.file_path if request else None) or _DEFAULT_SEED
    file_path = os.path.normpath(file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Seed file not found: {file_path}")

    from data.dedup_seeds import dedup_entries

    with open(file_path, encoding="utf-8") as f:
        raw_list = json.load(f)

    clean_list = dedup_entries(raw_list)

    results = []
    for entry in clean_list:
        name = entry["name"]
        existing = session.exec(
            select(PIProfile).where(PIProfile.name == name)
        ).first()
        if existing:
            print(f"[seed] Skipping '{name}' — already in database (id={existing.id})")
            results.append({"name": name, "status": "already_exists", "id": existing.id})
            continue

        item = PIProfileSeedItem(**entry)
        pi = PIProfile(**item.model_dump())
        session.add(pi)
        session.flush()  # get id before commit
        results.append({"name": pi.name, "status": "added", "id": pi.id})

    session.commit()
    return {"seeded": results, "total": len(results)}
