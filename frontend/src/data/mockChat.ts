import type { ChemistryReport, TranscriptMessage } from '../types';
import { MOCK_MATCHES } from './mockMatches';

export const DEMO_SUGGESTED_OPENERS: string[] = [
  "Tell me about your recent NeurIPS paper on MSA-free diffusion.",
  "What's your lab's typical meeting cadence?",
  "How does funding work for international students in your group?",
];

export const DEMO_TRANSCRIPT: TranscriptMessage[] = [
  {
    role: 'pi',
    content:
      "Glad you reached out. I read through your background — the **MSA-free protein folding** work caught my eye, since we've been pushing in a similar direction. Quick question to start: when you curated your CATH subset, did you filter by structural novelty or by sequence diversity? The choice ends up mattering a lot for how the model generalizes.",
  },
  {
    role: 'student',
    content:
      "We filtered primarily by structural novelty — used TM-align to enforce a 0.5 cutoff against everything in the training set. The honest tradeoff was that we lost a lot of sequence diversity that way, and I think it hurt us on the long-tail families.",
  },
  {
    role: 'pi',
    content:
      "That's exactly the regime our **2024 NeurIPS paper** ran into. We ended up using a hybrid filter — structural novelty for the validation split, sequence diversity for training — and saw about a 6-point TM-score bump on the orphan families. Curious: how did you handle *evaluation* on the long tail, where ground-truth structures are basically nonexistent?",
  },
  {
    role: 'student',
    content:
      "We leaned on a self-consistency proxy — generate, refold with ESMFold, measure agreement. Imperfect but tractable. Can I ask something different? I'm trying to get a sense of how your lab actually runs day-to-day. What's the meeting cadence and how much independence do new students get?",
  },
  {
    role: 'pi',
    content:
      "Self-consistency is reasonable — we use a similar trick. On lab culture: I do **weekly 1:1s** with every student, plus a Monday group meeting. The first six months I'm fairly hands-on — picking projects, debugging code, reading drafts. After that, students drive their own direction and I move into more of a sounding-board role.\n\nI should be honest with you about one thing: I was on **sabbatical for spring 2025**, and a couple of my newer students felt I was less available than they wanted. I'm fully back now, but it's worth knowing.",
  },
  {
    role: 'student',
    content:
      "I appreciate you flagging that. One last thing — I'm an F1 student, and I noticed your lab has an active NSF grant. How does funding usually work for international students in your group?",
  },
  {
    role: 'pi',
    content:
      "Good question, and important. The NSF CAREER grant is **citizen-restricted** — that one wouldn't fund you directly. But we have a separate **Moore Foundation slot** that has no such restriction, and historically I've used it for international students. There's also TA funding for the first year, which everyone does anyway.\n\nI'm not 100% sure on the current Moore slot availability for fall — that can shift quarter to quarter. You'd want to confirm specifics with my lab manager, Sarah, before counting on it.",
  },
];

export function getDemoMatch(matchId: number) {
  return MOCK_MATCHES.find((m) => m.id === matchId) ?? MOCK_MATCHES[0];
}

export const DEMO_REPORT: ChemistryReport = {
  overall_score: 84,
  dimension_scores: {
    research_alignment: 92,
    mentorship_compatibility: 78,
    culture_fit: 84,
    communication_fit: 88,
    red_flags: 75,
  },
  dimension_rationale: {
    research_alignment:
      "Both you and Dr. Liu converged on **MSA-free protein folding** within the first exchange, and your CATH curation tradeoff matches the exact regime her 2024 NeurIPS paper addresses. The technical vocabulary aligned without prompting — strong signal of genuine overlap.",
    mentorship_compatibility:
      "Her stated structure (weekly 1:1s, hands-on for 6 months, then autonomy) maps closely to your independence preference of 4/5. The sabbatical caveat is a minor concern but not disqualifying — she's now back full-time.",
    culture_fit:
      "The conversation surfaced no friction on lab norms. Group meeting cadence and 1:1 frequency are within your stated preferences, and the technical register felt natural on both sides.",
    communication_fit:
      "Dr. Liu asked clarifying questions, admitted uncertainty twice without prompting, and pivoted gracefully when you changed topics. This is unusually direct and honest by PI standards — a strong working-relationship signal.",
    red_flags:
      "One concern: her **spring 2025 sabbatical** reportedly left newer students feeling under-supported. She volunteered this herself, which is a positive trust signal — but the impact on current student morale warrants a direct check.",
  },
  key_positives: [
    "Specific technical resonance — both you and Dr. Liu used 'long-tail families' unprompted and converged on the same evaluation challenge within two turns.",
    "Dr. Liu volunteered her sabbatical impact without being asked — a strong honesty signal that bodes well for working with her on hard problems.",
    "She immediately surfaced an alternative funding path (Moore Foundation) for your F1 status, instead of deflecting on the citizenship-restricted NSF grant.",
  ],
  key_concerns: [
    "Mentorship continuity post-sabbatical is unclear. Newer students reportedly felt under-supported during spring 2025; worth verifying with current students directly.",
    "Moore Foundation slot availability is uncertain quarter-to-quarter. Don't count on it as a funding plan until lab manager Sarah confirms in writing.",
  ],
  recommended_questions: [
    "Could I speak with one of your current senior students about their experience during the spring 2025 sabbatical?",
    "What's the realistic timeline for confirming the Moore Foundation slot for fall admits, and what happens if it falls through?",
    "Beyond NSF and Moore, are there backup funding paths for F1 students in your group — TA assignments, departmental fellowships?",
  ],
  pi_introduction_draft: `Subject: Prospective PhD applicant — MSA-free protein folding work

Dear Dr. Liu,

I'm a prospective PhD applicant in computational biology, and I came across your 2024 NeurIPS paper on MSA-free diffusion models for protein structure prediction. Your hybrid filtering approach — structural novelty for validation, sequence diversity for training — directly addresses a problem I ran into during my undergraduate research, where I trained an MSA-free model on a curated CATH subset and lost generalization on the long-tail families.

I'd love the opportunity to talk with you about your group's work and whether there might be a fit for my PhD. I'm especially interested in the evaluation question — how you think about ground truth in regimes where structures are sparse — and would value the chance to learn from your approach.

Would you be open to a 20-minute conversation in the next few weeks? I'm happy to work around your schedule.

Best,
[Your name]`,
};

