export interface StudentProfile {
  id?: number;
  name: string;
  gpa: number;
  field_of_study: string;
  research_background: string;
  technical_skills: string[];
  years_research_experience: number;
  has_publications: boolean;
  cv_text?: string;
  known_professors: string[];
  preferred_research_topics: string[];
  location_preference: 'west_coast' | 'east_coast' | 'midwest' | 'any';
  citizenship_status: 'us_citizen' | 'pr' | 'f1' | 'j1' | 'other';
  min_stipend?: number;
  preferred_lab_size: 'small' | 'medium' | 'large';
  independence_preference: number;
  intervention_tolerance: number;
  meeting_frequency_preference: number;
  work_life_balance_importance: number;
  industry_connections_importance: number;
  publication_rate_importance: number;
}

export interface NSFGrant {
  title: string;
  amount: number;
  expiry_date: string;
  citizen_only: boolean;
}

export interface PIProfile {
  id?: number;
  name: string;
  institution: string;
  department: string;
  email?: string;
  lab_website?: string;
  semantic_scholar_id?: string;
  research_areas: string[];
  recent_abstracts: string[];
  co_author_ids: string[];
  papers_last_12_months: number;
  nsf_grants: NSFGrant[];
  has_active_nsf_grant: boolean;
  total_active_funding_usd?: number;
  funding_citizen_restricted: boolean;
  tier: number;
  location: string;
  lab_size: number;
  is_recruiting: boolean;
  pi_survey?: Record<string, unknown>;
  student_survey_responses: Record<string, unknown>[];
  reply_likelihood?: 'high' | 'medium' | 'low';
}

export interface TranscriptMessage {
  role: 'pi' | 'student';
  content: string;
}

export interface MatchResult {
  id?: number;
  student_id: number;
  pi_id: number;
  research_direction_score: number;
  mentorship_style_score: number;
  funding_stability_score: number;
  culture_fit_score: number;
  technical_skills_score: number;
  location_score: number;
  is_direct_connection: boolean;
  is_indirect_connection: boolean;
  indirect_connection_via?: string;
  citizenship_mismatch: boolean;
  research_match_rationale: string;
  reply_likelihood: 'high' | 'medium' | 'low';
  overall_score: number;
  transcript?: TranscriptMessage[];
  chemistry_report?: ChemistryReport;
  pi?: PIProfile;
}

export interface ChemistryReport {
  overall_score: number;
  dimension_scores: {
    research_alignment: number;
    mentorship_compatibility: number;
    culture_fit: number;
    communication_fit: number;
    red_flags: number;
  };
  dimension_rationale: {
    research_alignment: string;
    mentorship_compatibility: string;
    culture_fit: string;
    communication_fit: string;
    red_flags: string;
  };
  key_positives: string[];
  key_concerns: string[];
  recommended_questions: string[];
  pi_introduction_draft: string;
}

export interface SimulateRequest {
  message: string;
}
