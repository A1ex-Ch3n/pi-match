import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { MatchResult, PIProfile } from '../types';
import FlagBadge from './FlagBadge';

interface PICardProps {
  match: MatchResult;
  pi: PIProfile;
  rank: number;
}

const REPLY_COLORS = {
  high: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-red-100 text-red-700',
};

function scoreTier(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 65) return 'Strong';
  if (score >= 50) return 'Moderate';
  if (score >= 35) return 'Weak';
  return 'Poor';
}

function mentorshipRationale(score: number): string {
  if (score >= 80) return 'Your independence, meeting frequency, and involvement preferences align closely with this PI\'s stated advising style.';
  if (score >= 60) return 'Your mentorship preferences broadly match this PI\'s style, with some differences in autonomy or meeting cadence.';
  if (score >= 40) return 'There are notable gaps between your preferred advising style and what this PI typically offers.';
  return 'Your mentorship expectations differ significantly from this PI\'s documented approach — worth discussing directly.';
}

function fundingRationale(score: number, pi: PIProfile): string {
  const parts: string[] = [];
  if (pi.has_active_nsf_grant) parts.push('Active NSF grant');
  if ((pi.total_active_funding_usd ?? 0) >= 500_000) parts.push(`$${((pi.total_active_funding_usd ?? 0) / 1000).toFixed(0)}K total funding`);
  else if ((pi.total_active_funding_usd ?? 0) > 0) parts.push(`$${((pi.total_active_funding_usd ?? 0) / 1000).toFixed(0)}K funding`);
  if (pi.is_recruiting) parts.push('actively recruiting');
  if (parts.length === 0) return 'No active NSF grant data found. Funding stability is uncertain — check their lab website.';
  return parts.join(', ') + '. ' + (score >= 70 ? 'Funding outlook is strong.' : 'Some funding uncertainty — verify before applying.');
}

function cultureRationale(score: number, pi: PIProfile): string {
  const size = pi.lab_size ?? 5;
  const sizeLabel = size <= 4 ? 'small' : size <= 12 ? 'medium' : 'large';
  if (score >= 70) return `Lab size (${size} members, ${sizeLabel}) fits your preference and culture alignment looks strong.`;
  if (score >= 50) return `Lab size is ${size} members (${sizeLabel}). Some mismatch with your stated lab size or work-life balance preferences.`;
  return `Lab size of ${size} members and/or work-life balance expectations may not match your preferences well.`;
}

function skillsRationale(score: number): string {
  if (score >= 75) return 'Strong overlap between your technical skills and the lab\'s research methods.';
  if (score >= 50) return 'Partial skill overlap. Some of your technical background transfers; you\'d need to develop new skills in the lab.';
  return 'Limited direct skill overlap detected. This could be a growth opportunity, or the technical gap may be significant.';
}

function ScoreBar({
  label, score, weight, rationale, isExpanded, onToggle
}: {
  label: string; score: number; weight: string; rationale: string;
  isExpanded: boolean; onToggle: () => void;
}) {
  const color = score >= 70 ? 'bg-violet-500' : score >= 50 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="rounded-lg overflow-hidden border border-transparent hover:border-gray-100 transition-colors">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-2 text-sm py-1 text-left"
      >
        <span className="w-24 text-gray-500 shrink-0">{label}</span>
        <div className="flex-1 bg-gray-100 rounded-full h-2">
          <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${score}%` }} />
        </div>
        <span className="w-8 text-right text-gray-700 font-medium text-xs">{score.toFixed(0)}</span>
        <span className="text-gray-400 text-xs w-8">{weight}</span>
        <span className="text-gray-300 text-xs">{isExpanded ? '▲' : '▼'}</span>
      </button>
      {isExpanded && (
        <div className="px-2 pb-2 pt-0.5">
          <div className="text-xs text-violet-700 font-medium mb-0.5">{scoreTier(score)} match</div>
          <p className="text-xs text-gray-500 leading-relaxed">{rationale}</p>
        </div>
      )}
    </div>
  );
}

export default function PICard({ match, pi, rank }: PICardProps) {
  const replyClass = REPLY_COLORS[match.reply_likelihood] ?? REPLY_COLORS.medium;
  const [expanded, setExpanded] = useState<string | null>(null);
  const toggle = (key: string) => setExpanded(prev => prev === key ? null : key);

  const scores = [
    {
      key: 'research', label: 'Research', score: match.research_direction_score, weight: '40%',
      rationale: match.research_match_rationale || 'No research rationale available.',
    },
    {
      key: 'mentorship', label: 'Mentorship', score: match.mentorship_style_score, weight: '20%',
      rationale: mentorshipRationale(match.mentorship_style_score),
    },
    {
      key: 'funding', label: 'Funding', score: match.funding_stability_score, weight: '15%',
      rationale: fundingRationale(match.funding_stability_score, pi),
    },
    {
      key: 'culture', label: 'Culture', score: match.culture_fit_score, weight: '10%',
      rationale: cultureRationale(match.culture_fit_score, pi),
    },
    {
      key: 'skills', label: 'Skills', score: match.technical_skills_score, weight: '10%',
      rationale: skillsRationale(match.technical_skills_score),
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-violet-100 text-violet-700 font-bold text-lg flex items-center justify-center shrink-0">
            {rank}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-lg leading-tight">{pi.name}</h3>
            <p className="text-sm text-gray-500">{pi.department} · {pi.institution}</p>
            {pi.lab_website && (
              <a href={pi.lab_website} target="_blank" rel="noopener noreferrer"
                className="text-xs text-violet-600 hover:underline">
                Lab website ↗
              </a>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-3xl font-bold text-violet-700">{match.overall_score.toFixed(0)}</div>
          <div className="text-xs text-gray-400">/ 100</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {match.is_direct_connection && <FlagBadge type="direct" />}
        {match.is_indirect_connection && <FlagBadge type="indirect" via={match.indirect_connection_via} />}
        {match.citizenship_mismatch && <FlagBadge type="citizenship" />}
        {pi.has_active_nsf_grant && <FlagBadge type="funding" />}
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${replyClass}`}>
          Reply: {match.reply_likelihood}
        </span>
      </div>

      <div className="flex flex-wrap gap-1 mb-4">
        {(pi.research_areas ?? []).slice(0, 4).map(area => (
          <span key={area} className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">{area}</span>
        ))}
      </div>

      <div className="space-y-0.5 mb-4">
        <p className="text-xs text-gray-400 mb-1">Click any score to see why ▾</p>
        {scores.map(({ key, label, score, weight, rationale }) => (
          <ScoreBar
            key={key}
            label={label}
            score={score}
            weight={weight}
            rationale={rationale}
            isExpanded={expanded === key}
            onToggle={() => toggle(key)}
          />
        ))}
      </div>

      <div className="flex gap-2">
        {match.id && (
          <Link to={`/chat/${match.id}`}
            className="flex-1 text-center bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors">
            Chat with PI Avatar
          </Link>
        )}
        {match.transcript && match.transcript.length > 0 && match.id && (
          <Link to={`/report/${match.id}`}
            className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg transition-colors">
            View Report
          </Link>
        )}
      </div>
    </div>
  );
}
