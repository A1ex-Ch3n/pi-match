import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getReport } from '../api/client';
import type { ChemistryReport, MatchResult } from '../types';
import ScoreRadar, { chemistryRadarDimensions } from '../components/ScoreRadar';

export default function ReportPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const [report, setReport] = useState<ChemistryReport | null>(null);
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!matchId) return;
    getReport(Number(matchId))
      .then(data => {
        setMatch(data.match);
        setReport(data.report);
      })
      .catch(() => setError('Could not load report.'))
      .finally(() => setLoading(false));
  }, [matchId]);

  async function copyEmail() {
    if (!report?.pi_introduction_draft) return;
    await navigator.clipboard.writeText(report.pi_introduction_draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Report not found.'}</p>
          <Link to="/" className="text-violet-600 hover:underline text-sm">← Go home</Link>
        </div>
      </div>
    );
  }

  const piName = match?.pi?.name ?? 'PI';
  const radarData = chemistryRadarDimensions(report.dimension_scores);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div className="mb-6">
          <Link
            to={`/chat/${matchId}`}
            className="text-sm text-violet-600 hover:underline"
          >
            ← Back to Chat
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">Chemistry Report</h1>
          <p className="text-gray-500 text-sm">with {piName}</p>
        </div>

        {/* Overall Score */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-4 text-center">
          <div className="text-6xl font-bold text-violet-700 mb-1">
            {report.overall_score.toFixed(0)}
          </div>
          <div className="text-gray-400 text-sm">Overall Chemistry Score / 100</div>
        </div>

        {/* Radar Chart */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-4">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Dimension Breakdown</h2>
          <ScoreRadar dimensions={radarData} />
          <div className="mt-4 space-y-3">
            {(Object.entries(report.dimension_scores) as [string, number][]).map(([key, score]) => (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-medium text-gray-800">{score.toFixed(0)}/100</span>
                </div>
                <div className="bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-violet-500 h-1.5 rounded-full"
                    style={{ width: `${score}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  {report.dimension_rationale[key as keyof typeof report.dimension_rationale]}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Positives & Concerns */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-emerald-50 rounded-2xl border border-emerald-100 p-5">
            <h2 className="text-sm font-semibold text-emerald-800 mb-3">Key Positives</h2>
            <ul className="space-y-2">
              {report.key_positives.map((item, i) => (
                <li key={i} className="text-sm text-emerald-700 flex gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-amber-50 rounded-2xl border border-amber-100 p-5">
            <h2 className="text-sm font-semibold text-amber-800 mb-3">Key Concerns</h2>
            <ul className="space-y-2">
              {report.key_concerns.map((item, i) => (
                <li key={i} className="text-sm text-amber-700 flex gap-2">
                  <span className="text-amber-400 mt-0.5">!</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recommended Questions */}
        {report.recommended_questions.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-4">
            <h2 className="text-base font-semibold text-gray-900 mb-3">Questions to Ask</h2>
            <ul className="space-y-2">
              {report.recommended_questions.map((q, i) => (
                <li key={i} className="text-sm text-gray-600 flex gap-2">
                  <span className="text-violet-400 font-bold shrink-0">{i + 1}.</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Intro Email Draft */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-gray-900">Introduction Email Draft</h2>
            <button
              onClick={copyEmail}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg transition-colors font-medium"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed border border-gray-100">
            {report.pi_introduction_draft}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Review and personalize before sending. This is a draft — do not send as-is.
          </p>
        </div>
      </div>
    </div>
  );
}
