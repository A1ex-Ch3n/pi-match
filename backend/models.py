from typing import Optional, List, Any
from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field


class StudentProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Academic
    name: str
    gpa: float = Field(default=0.0)
    field_of_study: str
    research_background: str = Field(default="")
    technical_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    years_research_experience: int = Field(default=0)
    has_publications: bool = Field(default=False)
    cv_text: Optional[str] = Field(default=None)

    # Connections
    known_professors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    # Preferences
    preferred_research_topics: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    location_preference: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    citizenship_status: str = Field(default="other")
    min_stipend: Optional[int] = Field(default=None)
    preferred_lab_size: str = Field(default="any")

    # Sliders (1–5 scale)
    independence_preference: int = Field(default=3)
    intervention_tolerance: int = Field(default=3)
    meeting_frequency_preference: int = Field(default=3)
    work_life_balance_importance: int = Field(default=3)
    industry_connections_importance: int = Field(default=3)
    publication_rate_importance: int = Field(default=3)


class PIProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Identity
    name: str
    institution: str
    department: str
    email: Optional[str] = Field(default=None)
    lab_website: Optional[str] = Field(default=None)

    # Research
    semantic_scholar_id: Optional[str] = Field(default=None)
    research_areas: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    recent_abstracts: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    co_author_ids: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    co_author_names: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    papers_last_12_months: int = Field(default=0)
    papers: Optional[List[Any]] = Field(default=None, sa_column=Column(JSON))

    # Funding
    nsf_grants: Optional[List[Any]] = Field(default=None, sa_column=Column(JSON))
    has_active_nsf_grant: bool = Field(default=False)
    total_active_funding_usd: Optional[int] = Field(default=None)
    funding_citizen_restricted: bool = Field(default=False)

    # Classification
    tier: int = Field(default=3)
    location: str = Field(default="")
    lab_size: int = Field(default=5)
    is_recruiting: bool = Field(default=True)

    # Avatar inputs
    pi_survey: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    student_survey_responses: Optional[List[Any]] = Field(default=None, sa_column=Column(JSON))

    # Computed
    reply_likelihood: Optional[str] = Field(default=None)


class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="studentprofile.id")
    pi_id: int = Field(foreign_key="piprofile.id")

    # Dimension scores (0–100)
    research_direction_score: float = Field(default=0.0)
    mentorship_style_score: float = Field(default=0.0)
    funding_stability_score: float = Field(default=0.0)
    culture_fit_score: float = Field(default=0.0)
    technical_skills_score: float = Field(default=0.0)
    location_score: float = Field(default=0.0)

    # Connection bonuses
    is_direct_connection: bool = Field(default=False)
    is_indirect_connection: bool = Field(default=False)
    indirect_connection_via: Optional[str] = Field(default=None)

    # Flags
    citizenship_mismatch: bool = Field(default=False)

    # AI content
    research_match_rationale: str = Field(default="")
    reply_likelihood: str = Field(default="medium")

    # Overall
    overall_score: float = Field(default=0.0)

    # v2.0+
    transcript: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    chemistry_report: Optional[Any] = Field(default=None, sa_column=Column(JSON))
