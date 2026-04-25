from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from database import get_session
from models import StudentProfile
from schemas import StudentProfileCreate, StudentProfileResponse

router = APIRouter()


@router.post("/survey", response_model=StudentProfileResponse, status_code=201)
def submit_survey(data: StudentProfileCreate, session: Session = Depends(get_session)):
    profile = StudentProfile(**data.model_dump())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/survey/{student_id}", response_model=StudentProfileResponse)
def get_student(student_id: int, session: Session = Depends(get_session)):
    profile = session.get(StudentProfile, student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return profile
