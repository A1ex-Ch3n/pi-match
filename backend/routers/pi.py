import json
import os
from typing import List, Optional

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

    with open(file_path, encoding="utf-8") as f:
        raw_list = json.load(f)

    results = []
    for entry in raw_list:
        existing = session.exec(
            select(PIProfile).where(PIProfile.name == entry.get("name", ""))
        ).first()
        if existing:
            results.append({"name": entry.get("name"), "status": "already_exists", "id": existing.id})
            continue

        item = PIProfileSeedItem(**entry)
        pi = PIProfile(**item.model_dump())
        session.add(pi)
        session.flush()  # get id before commit
        results.append({"name": pi.name, "status": "added", "id": pi.id})

    session.commit()
    return {"seeded": results, "total": len(results)}
