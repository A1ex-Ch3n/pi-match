import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMatches } from '../api/client';
import type { MatchResult, PIProfile } from '../types';
import PICard from '../components/PICard';

interface MatchWithPI extends MatchResult {
  pi: PIProfile;
}

export default function MatchPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [matches, setMatches] = useState<MatchWithPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!studentId) return;
    loadMatches();
  }, [studentId]);

  async function loadMatches() {
    try {
      const data = await getMatches(Number(studentId));
      setMatches(data as MatchWithPI[]);
    } catch {
      setError('Could not load matches. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  const sorted = [...matches].sort((a, b) => {
    if (a.is_direct_connection && !b.is_direct_connection) return -1;
    if (!a.is_direct_connection && b.is_direct_connection) return 1;
    return b.overall_score - a.overall_score;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link to="/" className="text-sm text-violet-600 hover:underline">← New Search</Link>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Your PI Matches</h1>
            {!loading && matches.length > 0 && (
              <p className="text-sm text-gray-500 mt-1">{matches.length} professors ranked by fit</p>
            )}
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Running AI matching...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {!loading && matches.length === 0 && !error && (
          <div className="text-center py-24 text-gray-400">
            <p className="text-lg mb-4">No matches yet.</p>
            <Link to="/" className="bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-6 py-2.5 rounded-lg">
              Start a new search
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {sorted.map((match, i) => (
            <PICard
              key={match.id ?? i}
              match={match}
              pi={match.pi}
              rank={i + 1}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
