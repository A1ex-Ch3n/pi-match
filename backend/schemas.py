from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class StudentProfileCreate(BaseModel):
    name: str
    gpa: float
    field_of_study: str
    research_background: str
    technical_skills: List[str] = []
    years_research_experience: int = 0
    has_publications: bool = False
    cv_text: Optional[str] = None
    known_professors: List[str] = []
    preferred_research_topics: List[str] = []
    location_preference: List[str] = ["any"]
    citizenship_status: str
    min_stipend: Optional[int] = None
    preferred_lab_size: str = "any"
    independence_preference: int = 3
    intervention_tolerance: int = 3
    meeting_frequency_preference: int = 3
    work_life_balance_importance: int = 3
    industry_connections_importance: int = 3
    publication_rate_importance: int = 3


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int]
    name: str
    gpa: float
    field_of_study: str
    research_background: str
    technical_skills: Optional[List[str]]
    years_research_experience: int
    has_publications: bool
    cv_text: Optional[str]
    known_professors: Optional[List[str]]
    preferred_research_topics: Optional[List[str]]
    location_preference: Optional[List[str]]
    citizenship_status: str
    min_stipend: Optional[int]
    preferred_lab_size: str
    independence_preference: int
    intervention_tolerance: int
    meeting_frequency_preference: int
    work_life_balance_importance: int
    industry_connections_importance: int
    publication_rate_importance: int


class PIProfileResponse(BaseModel):
    """Public PI profile — student_survey_responses intentionally excluded."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int]
    name: str
    institution: str
    department: str
    email: Optional[str]
    lab_website: Optional[str]
    semantic_scholar_id: Optional[str]
    research_areas: Optional[List[str]]
    recent_abstracts: Optional[List[str]]
    co_author_ids: Optional[List[str]]
    co_author_names: Optional[List[str]]
    papers_last_12_months: int
    nsf_grants: Optional[List[Any]]
    has_active_nsf_grant: bool
    total_active_funding_usd: Optional[int]
    funding_citizen_restricted: bool
    tier: int
    location: str
    lab_size: int
    is_recruiting: bool
    pi_survey: Optional[Dict]
    reply_likelihood: Optional[str]


class PIProfileSeedItem(BaseModel):
    name: str
    institution: str
    department: str
    email: Optional[str] = None
    lab_website: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    research_areas: List[str] = []
    recent_abstracts: List[str] = []
    co_author_ids: List[str] = []
    co_author_names: List[str] = []
    papers_last_12_months: int = 0
    nsf_grants: List[Any] = []
    has_active_nsf_grant: bool = False
    total_active_funding_usd: Optional[int] = None
    funding_citizen_restricted: bool = False
    tier: int = 3
    location: str = ""
    lab_size: int = 5
    is_recruiting: bool = True
    pi_survey: Optional[Dict] = None
    student_survey_responses: Optional[List[Any]] = None
    reply_likelihood: Optional[str] = None
    papers: Optional[List[Dict]] = None


class SeedRequest(BaseModel):
    file_path: Optional[str] = None


class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int]
    student_id: int
    pi_id: int
    research_direction_score: float
    mentorship_style_score: float
    funding_stability_score: float
    culture_fit_score: float
    technical_skills_score: float
    location_score: float
    is_direct_connection: bool
    is_indirect_connection: bool
    indirect_connection_via: Optional[str]
    citizenship_mismatch: bool
    research_match_rationale: str
    reply_likelihood: str
    overall_score: float
    transcript: Optional[List[Dict]]
    chemistry_report: Optional[Dict]
    pi: Optional[PIProfileResponse] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    pi_response: str
    transcript: List[Dict[str, str]]
    match_id: int


class ChemistryReportSchema(BaseModel):
    overall_score: float
    dimension_scores: Dict[str, float]
    dimension_rationale: Dict[str, str]
    key_positives: List[str]
    key_concerns: List[str]
    recommended_questions: List[str]
    pi_introduction_draft: str
