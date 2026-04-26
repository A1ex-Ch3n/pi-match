import type { MatchResult, PIProfile } from '../types';

export interface MockMatchWithPI extends MatchResult {
  pi: PIProfile;
}

const basePI = (overrides: Partial<PIProfile>): PIProfile => ({
  name: '',
  institution: 'Caltech',
  department: '',
  email: undefined,
  lab_website: undefined,
  semantic_scholar_id: undefined,
  research_areas: [],
  recent_abstracts: [],
  co_author_ids: [],
  papers_last_12_months: 0,
  nsf_grants: [],
  has_active_nsf_grant: false,
  total_active_funding_usd: undefined,
  funding_citizen_restricted: false,
  tier: 1,
  location: 'CA',
  lab_size: 8,
  is_recruiting: true,
  pi_survey: undefined,
  student_survey_responses: [],
  reply_likelihood: 'medium',
  ...overrides,
});

const baseMatch = (overrides: Partial<MockMatchWithPI>): MockMatchWithPI => ({
  id: 0,
  student_id: 0,
  pi_id: 0,
  research_direction_score: 70,
  mentorship_style_score: 70,
  funding_stability_score: 70,
  culture_fit_score: 70,
  technical_skills_score: 70,
  location_score: 100,
  is_direct_connection: false,
  is_indirect_connection: false,
  indirect_connection_via: undefined,
  citizenship_mismatch: false,
  research_match_rationale: '',
  reply_likelihood: 'medium',
  overall_score: 70,
  transcript: undefined,
  chemistry_report: undefined,
  pi: basePI({}),
  ...overrides,
});

export const MOCK_MATCHES: MockMatchWithPI[] = [
  // 1 — HERO: full-pentagon fingerprint, direct connection, active funding, long markdown rationale
  baseMatch({
    id: 1,
    pi_id: 1,
    research_direction_score: 92,
    mentorship_style_score: 86,
    funding_stability_score: 78,
    culture_fit_score: 82,
    technical_skills_score: 88,
    overall_score: 88,
    is_direct_connection: true,
    reply_likelihood: 'high',
    research_match_rationale:
      "Dr. Liu's **2024 NeurIPS paper** on diffusion-based protein structure prediction is a near-perfect mirror of the work you described. Her lab's recent shift from MSA-based to **MSA-free embeddings** — the exact problem you tackled in your undergraduate research — places you at the intersection of two of her active research directions. Three of her last five papers cite techniques you've already used; one explicitly proposes the curated-CATH evaluation regime you mention in your background.",
    pi: basePI({
      id: 1,
      name: 'Dr. Karen Liu',
      department: 'Computational Biology',
      lab_website: 'https://liu-lab.caltech.edu',
      research_areas: ['Generative Models', 'Protein Structure', 'Diffusion', 'Genomics'],
      papers_last_12_months: 9,
      has_active_nsf_grant: true,
      total_active_funding_usd: 1_250_000,
      lab_size: 11,
      reply_likelihood: 'high',
    }),
  }),

  // 2 — Stretched fingerprint: research strong, mentorship weak. Indirect connection.
  baseMatch({
    id: 2,
    pi_id: 2,
    research_direction_score: 84,
    mentorship_style_score: 58,
    funding_stability_score: 85,
    culture_fit_score: 75,
    technical_skills_score: 72,
    overall_score: 79,
    is_indirect_connection: true,
    indirect_connection_via: 'Prof. John Smith',
    reply_likelihood: 'medium',
    research_match_rationale:
      "Dr. Rao's **reinforcement learning for robotic manipulation** work overlaps moderately with your background. His **ICRA 2025 paper** on sample-efficient RL aligns with your stated interest in robotics, though your protein-focused background is a slight stretch for his current research direction.",
    pi: basePI({
      id: 2,
      name: 'Dr. Manish Rao',
      department: 'Computing & Mathematical Sciences',
      lab_website: 'https://rao-lab.caltech.edu',
      research_areas: ['Reinforcement Learning', 'Robotics', 'Sim2Real'],
      papers_last_12_months: 7,
      has_active_nsf_grant: true,
      total_active_funding_usd: 850_000,
      lab_size: 14,
      reply_likelihood: 'medium',
    }),
  }),

  // 3 — Balanced mid fingerprint, citizenship mismatch flag (key demo flag per CLAUDE.md)
  baseMatch({
    id: 3,
    pi_id: 3,
    research_direction_score: 72,
    mentorship_style_score: 78,
    funding_stability_score: 82,
    culture_fit_score: 68,
    technical_skills_score: 64,
    overall_score: 74,
    citizenship_mismatch: true,
    reply_likelihood: 'low',
    research_match_rationale:
      "Some overlap with Dr. Brown's **cryo-EM and protein design** work, but her lab's wet-lab focus may not align with your computational background. Her current DOD-funded grants restrict participation to US citizens.",
    pi: basePI({
      id: 3,
      name: 'Dr. Aisha Brown',
      department: 'Bioengineering',
      lab_website: 'https://brown-lab.caltech.edu',
      research_areas: ['Cryo-EM', 'Protein Design', 'Wet Lab'],
      papers_last_12_months: 5,
      has_active_nsf_grant: false,
      total_active_funding_usd: 2_100_000,
      funding_citizen_restricted: true,
      lab_size: 7,
      reply_likelihood: 'low',
    }),
  }),

  // 4 — Contracted, irregular fingerprint: weak overall (tests clay color threshold)
  baseMatch({
    id: 4,
    pi_id: 4,
    research_direction_score: 58,
    mentorship_style_score: 52,
    funding_stability_score: 42,
    culture_fit_score: 66,
    technical_skills_score: 48,
    overall_score: 55,
    reply_likelihood: 'low',
    research_match_rationale:
      'Limited overlap detected. Dr. Chen\'s **mathematical foundations** work is rigorous but tangential to applied computational biology.',
    pi: basePI({
      id: 4,
      name: 'Dr. Wei Chen',
      department: 'Computing & Mathematical Sciences',
      research_areas: ['Optimization Theory', 'Convex Analysis'],
      papers_last_12_months: 3,
      has_active_nsf_grant: false,
      total_active_funding_usd: 0,
      lab_size: 4,
      reply_likelihood: 'low',
    }),
  }),

  // 5 — Balanced moderate, no flags at all (baseline layout test)
  baseMatch({
    id: 5,
    pi_id: 5,
    research_direction_score: 68,
    mentorship_style_score: 72,
    funding_stability_score: 70,
    culture_fit_score: 74,
    technical_skills_score: 66,
    overall_score: 70,
    reply_likelihood: 'medium',
    research_match_rationale:
      "Dr. Patel's recent papers on **sequence modeling** show partial overlap with your background. Strong methodological fit on the modeling side, though her lab's focus on natural language sequences differs from your protein-sequence orientation.",
    pi: basePI({
      id: 5,
      name: 'Dr. Priya Patel',
      department: 'Computing & Mathematical Sciences',
      lab_website: 'https://patel-lab.caltech.edu',
      research_areas: ['NLP', 'Sequence Modeling', 'Transformers'],
      papers_last_12_months: 6,
      has_active_nsf_grant: false,
      total_active_funding_usd: 320_000,
      lab_size: 9,
      reply_likelihood: 'medium',
    }),
  }),
];
