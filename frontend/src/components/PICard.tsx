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

function ScoreBar({ label, score, weight }: { label: string; score: number; weight: string }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-28 text-gray-500 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className="bg-violet-500 h-2 rounded-full transition-all"
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="w-10 text-right text-gray-700 font-medium">{score.toFixed(0)}</span>
      <span className="text-gray-400 text-xs w-8">{weight}</span>
    </div>
  );
}

export default function PICard({ match, pi, rank }: PICardProps) {
  const replyClass = REPLY_COLORS[match.reply_likelihood] ?? REPLY_COLORS.medium;

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
              <a
                href={pi.lab_website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-violet-600 hover:underline"
              >
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
        {match.is_indirect_connection && (
          <FlagBadge type="indirect" via={match.indirect_connection_via} />
        )}
        {match.citizenship_mismatch && <FlagBadge type="citizenship" />}
        {pi.has_active_nsf_grant && <FlagBadge type="funding" />}
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${replyClass}`}>
          Reply: {match.reply_likelihood}
        </span>
      </div>

      <div className="flex flex-wrap gap-1 mb-4">
        {pi.research_areas.slice(0, 4).map(area => (
          <span key={area} className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
            {area}
          </span>
        ))}
      </div>

      <div className="space-y-1.5 mb-4">
        <ScoreBar label="Research" score={match.research_direction_score} weight="40%" />
        <ScoreBar label="Mentorship" score={match.mentorship_style_score} weight="20%" />
        <ScoreBar label="Funding" score={match.funding_stability_score} weight="15%" />
        <ScoreBar label="Culture" score={match.culture_fit_score} weight="10%" />
        <ScoreBar label="Skills" score={match.technical_skills_score} weight="10%" />
      </div>

      <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 mb-4 leading-relaxed">
        {match.research_match_rationale}
      </p>

      <div className="flex gap-2">
        {match.id && (
          <Link
            to={`/chat/${match.id}`}
            className="flex-1 text-center bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Chat with PI Avatar
          </Link>
        )}
        {match.transcript && match.transcript.length > 0 && match.id && (
          <Link
            to={`/report/${match.id}`}
            className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg transition-colors"
          >
            View Report
          </Link>
        )}
      </div>
    </div>
  );
}
