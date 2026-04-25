import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
from backend.database import get_session
from backend.models import StudentProfile
from backend.schemas import StudentProfileCreate, StudentProfileResponse

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


@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """
    Accepts a .txt, .pdf, or .docx file and returns extracted text.
    The frontend can then populate cv_text and/or research_background from the result.
    """
    filename = file.filename or ""
    content = await file.read()

    # Normalise content-type: strip charset suffixes like "text/plain; charset=utf-8"
    ct = (file.content_type or "").split(";")[0].strip()

    # Plain text
    if filename.endswith(".txt") or ct in ("text/plain", "application/text"):
        try:
            cv_text = content.decode("utf-8", errors="replace")
            return {"cv_text": cv_text.strip()}
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read text file.")

    # PDF — try pdfplumber, fall back gracefully
    if filename.endswith(".pdf") or ct == "application/pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            cv_text = "\n".join(pages).strip()
            if not cv_text:
                raise HTTPException(status_code=422, detail="PDF appears to be image-only or empty. Please paste your CV text manually.")
            return {"cv_text": cv_text}
        except ImportError:
            # pdfplumber not installed — instruct user to paste text
            raise HTTPException(
                status_code=501,
                detail="PDF parsing not available. Run `pip install pdfplumber --break-system-packages` on the server, or paste your CV text manually."
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {str(e)}")

    # DOCX
    if filename.endswith(".docx") or file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            cv_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return {"cv_text": cv_text.strip()}
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="DOCX parsing not available. Run `pip install python-docx --break-system-packages`, or paste your CV text manually."
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse DOCX: {str(e)}")

    raise HTTPException(
        status_code=415,
        detail="Unsupported file type. Please upload a .txt, .pdf, or .docx file."
    )
