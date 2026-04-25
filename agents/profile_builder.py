"""
profile_builder.py

Validates and merges PI profile data with survey responses into a structured AvatarProfile.
Assigns pipeline_type (PI_and_student, PI_only, public_only) based on data availability.

Pipeline types:
- PI_and_student: Both PI survey + student survey responses present and valid
- PI_only: Only PI survey present and valid
- public_only: No survey data, or surveys invalid/missing
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from backend.models import PIProfile


class PipelineType(str, Enum):
    """Avatar pipeline types based on survey data availability."""
    PI_AND_STUDENT = "PI_and_student"
    PI_ONLY = "PI_only"
    PUBLIC_ONLY = "public_only"


# ============================================================================
# Data Class: AvatarProfile
# ============================================================================

@dataclass
class AvatarProfile:
    """
    Validated, merged profile ready for avatar system prompt generation.
    
    Attributes:
        # Base identity (always present)
        id: PIProfile database ID
        name, institution, department: Core identity
        
        # Research data (always present)
        research_areas: List of research focus areas
        recent_abstracts: Recent paper abstracts for semantic matching
        papers: Full paper list with URLs
        co_author_names: Lab collaborators
        
        # Funding & lab info (always present)
        nsf_grants: List of NSF grant dicts
        lab_size: Approximate lab member count
        is_recruiting: Whether lab is accepting new students
        
        # Survey data (may be empty per pipeline)
        pi_survey: Dict of PI's survey responses (empty if not available)
        student_survey_responses: List of student survey responses (empty if not available)
        
        # Pipeline metadata
        pipeline_type: Which survey data is available
        survey_validation: Results of survey validation
        survey_metadata: Summary stats (e.g., student count, pi_valid, student_valid)
    """

    # Base identity
    id: int
    name: str
    institution: str
    department: str

    # Research data
    research_areas: List[str]
    recent_abstracts: List[str]
    papers: List[Dict[str, Any]]
    co_author_names: Optional[List[str]]

    # Funding & lab
    nsf_grants: Optional[List[Dict[str, Any]]]
    lab_size: int
    is_recruiting: bool

    # Survey data (may be empty)
    pi_survey: Dict[str, Any] = field(default_factory=dict)
    student_survey_responses: List[Dict[str, Any]] = field(default_factory=list)

    # Pipeline & metadata
    pipeline_type: PipelineType = PipelineType.PUBLIC_ONLY
    survey_validation: Dict[str, Any] = field(default_factory=dict)
    survey_metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Validation Functions
# ============================================================================

# Expected keys for PI survey (at least one required; others fill in detail)
PI_SURVEY_EXPECTED_KEYS = {
    "research_priorities",
    "mentorship_style",
    "meeting_frequency",
    "lab_expectations",
    "student_qualities",
    "autonomy_style",
    "intervention_level",
    "work_life_balance",
}

# Expected keys for each student survey response
STUDENT_SURVEY_EXPECTED_KEYS = {
    "overall_experience",
    "mentorship",
    "work_life_balance",
    "publication_rate",
    "lab_culture",
}


def _validate_pi_survey(pi_survey: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate PI survey completeness.
    
    Args:
        pi_survey: Dict of PI survey responses, or None
        
    Returns:
        (is_valid, error_list)
        - is_valid: True if survey is present and has reasonable content
        - error_list: List of specific missing/invalid fields
    """
    errors: List[str] = []

    if pi_survey is None:
        errors.append("PI survey not provided")
        return False, errors

    if not isinstance(pi_survey, dict):
        errors.append(f"PI survey must be dict, got {type(pi_survey)}")
        return False, errors

    if len(pi_survey) == 0:
        errors.append("PI survey is empty dict")
        return False, errors

    # Check that at least some expected keys are present
    missing_keys = PI_SURVEY_EXPECTED_KEYS - set(pi_survey.keys())
    if len(missing_keys) > 4:  # Allow up to 4 missing (i.e., at least 4 must be present)
        errors.append(
            f"PI survey missing too many fields: {missing_keys}. "
            f"Expected at least 4 of: {PI_SURVEY_EXPECTED_KEYS}"
        )
        return False, errors

    # Check that values are non-empty strings (basic content check)
    for key, value in pi_survey.items():
        if isinstance(value, str) and len(value.strip()) == 0:
            errors.append(f"PI survey field '{key}' is empty string")
        elif value is None:
            errors.append(f"PI survey field '{key}' is None")

    return len(errors) == 0, errors


def _validate_student_responses(
    responses: Optional[List[Dict[str, Any]]]
) -> Tuple[bool, List[str]]:
    """
    Validate student survey response list.
    
    Args:
        responses: List of student response dicts, or None
        
    Returns:
        (is_valid, error_list)
    """
    errors: List[str] = []

    if responses is None:
        errors.append("Student responses not provided")
        return False, errors

    if not isinstance(responses, list):
        errors.append(f"Student responses must be list, got {type(responses)}")
        return False, errors

    if len(responses) == 0:
        errors.append("Student responses list is empty")
        return False, errors

    # Each response should be a dict with expected keys
    for i, resp in enumerate(responses):
        if not isinstance(resp, dict):
            errors.append(f"Student response {i} is not a dict: {type(resp)}")
            continue

        missing_keys = STUDENT_SURVEY_EXPECTED_KEYS - set(resp.keys())
        if missing_keys:
            errors.append(
                f"Student response {i} missing fields: {missing_keys}"
            )

        # Check for empty values
        for key, value in resp.items():
            if isinstance(value, str) and len(value.strip()) == 0:
                errors.append(f"Student response {i}, field '{key}' is empty string")

    return len(errors) == 0, errors


def _extract_survey_metadata(
    pi_survey: Dict[str, Any],
    student_responses: List[Dict[str, Any]],
    pi_valid: bool,
    student_valid: bool,
) -> Dict[str, Any]:
    """
    Extract metadata about surveys for debugging and avatar behavior.
    
    Returns dict with keys:
    - pi_survey_valid: bool
    - student_survey_valid: bool
    - student_count: int
    - pi_survey_keys: list of keys present in pi_survey
    """
    return {
        "pi_survey_valid": pi_valid,
        "student_survey_valid": student_valid,
        "student_count": len(student_responses),
        "pi_survey_keys": list(pi_survey.keys()) if pi_survey else [],
    }


def _assign_pipeline_type(
    pi_valid: bool,
    student_valid: bool,
    override: Optional[str] = None,
) -> PipelineType:
    """
    Assign pipeline type based on survey validation results.
    
    Args:
        pi_valid: Is PI survey valid?
        student_valid: Are student responses valid?
        override: Force a specific pipeline type (for testing)
        
    Returns:
        PipelineType enum value
    """
    if override:
        try:
            return PipelineType(override)
        except ValueError:
            raise ValueError(
                f"Invalid pipeline_type override: {override}. "
                f"Must be one of: {[p.value for p in PipelineType]}"
            )

    if pi_valid and student_valid:
        return PipelineType.PI_AND_STUDENT
    elif pi_valid:
        return PipelineType.PI_ONLY
    else:
        return PipelineType.PUBLIC_ONLY


# ============================================================================
# Main Entry Point
# ============================================================================

def build_avatar_profile(
    pi_profile: PIProfile,
    override_pipeline_type: Optional[str] = None,
) -> AvatarProfile:
    """
    Build a validated AvatarProfile from a PIProfile.
    
    Validates both PI survey and student survey responses.
    Assigns pipeline_type automatically (unless overridden).
    Returns a structured AvatarProfile ready for pi_avatar.py formatting.
    
    Args:
        pi_profile: PIProfile instance from database
        override_pipeline_type: Force a specific pipeline type (for testing)
                               Must be one of: "PI_and_student", "PI_only", "public_only"
        
    Returns:
        AvatarProfile: Validated, structured profile with pipeline_type assigned
        
    Raises:
        ValueError: If override_pipeline_type is invalid
    """

    # Validate surveys
    pi_valid, pi_errors = _validate_pi_survey(pi_profile.pi_survey)
    student_valid, student_errors = _validate_student_responses(
        pi_profile.student_survey_responses
    )

    # Assign pipeline type
    pipeline_type = _assign_pipeline_type(pi_valid, student_valid, override_pipeline_type)

    # Extract metadata for debugging/avatar behavior
    metadata = _extract_survey_metadata(
        pi_profile.pi_survey or {},
        pi_profile.student_survey_responses or [],
        pi_valid,
        student_valid,
    )

    # Build validation report
    validation = {
        "pi_survey_valid": pi_valid,
        "pi_survey_errors": pi_errors,
        "student_responses_valid": student_valid,
        "student_response_errors": student_errors,
    }

    # Create AvatarProfile with appropriate survey data per pipeline
    if pipeline_type == PipelineType.PI_AND_STUDENT:
        pi_survey_data = pi_profile.pi_survey or {}
        student_responses_data = pi_profile.student_survey_responses or []
    elif pipeline_type == PipelineType.PI_ONLY:
        pi_survey_data = pi_profile.pi_survey or {}
        student_responses_data = []
    else:  # PUBLIC_ONLY
        pi_survey_data = {}
        student_responses_data = []

    avatar_profile = AvatarProfile(
        id=pi_profile.id,
        name=pi_profile.name,
        institution=pi_profile.institution,
        department=pi_profile.department,
        research_areas=pi_profile.research_areas or [],
        recent_abstracts=pi_profile.recent_abstracts or [],
        papers=pi_profile.papers or [],
        co_author_names=pi_profile.co_author_names,
        nsf_grants=pi_profile.nsf_grants,
        lab_size=pi_profile.lab_size or 5,
        is_recruiting=pi_profile.is_recruiting,
        pi_survey=pi_survey_data,
        student_survey_responses=student_responses_data,
        pipeline_type=pipeline_type,
        survey_validation=validation,
        survey_metadata=metadata,
    )

    return avatar_profile
