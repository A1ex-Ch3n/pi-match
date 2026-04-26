import { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMatches, runMatch } from '../api/client';
import type { MatchResult, PIProfile } from '../types';
import PICard from '../components/PICard';

interface MatchWithPI extends MatchResult {
  pi: PIProfile;
}

export default function MatchPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [matches, setMatches] = useState<MatchWithPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [matchingStatus, setMatchingStatus] = useState('Connecting to server…');
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0); // 0–100 for the bar width

  // Guard against React 18 StrictMode double-firing useEffect in dev
  const hasStarted = useRef(false);

  useEffect(() => {
    if (!studentId || hasStarted.current) return;
    hasStarted.current = true;
    loadOrRun();
  }, [studentId]);

  async function loadOrRun() {
    setLoading(true);
    setError('');

    // Wake Render if sleeping — wait up to 40s for it to respond
    const base = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace('/api', '');
    try {
      setMatchingStatus('Connecting to server…');
      await Promise.race([
        fetch(`${base}/health`),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 40000)),
      ]);
    } catch {
      // If still unreachable after 40s, show error with retry
      setLoading(false);
      setError('Cannot reach the server. If running locally, start uvicorn first. On production, wait 30 s and click Retry.');
      return;
    }

    try {
      setMatchingStatus('Loading matches…');
      const existing = await getMatches(Number(studentId));
      if (existing.length > 0) {
        setMatches(existing as MatchWithPI[]);
        setLoading(false);
        return;
      }
      setMatchingStatus('Scoring professors…');
      setProgress(0);

      // Animate progress bar from 0 → 90% over 20s while runMatch is in flight
      const startTime = Date.now();
      const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const estimated = Math.min(90, (elapsed / 20000) * 90);
        setProgress(estimated);
      }, 200);

      try {
        const fresh = await runMatch(Number(studentId));
        clearInterval(progressInterval);
        setProgress(100);
        setMatchingStatus('Done!');
        if (fresh.length === 0) localStorage.removeItem('lastStudentId');
        setMatches(fresh as MatchWithPI[]);
      } catch (err: unknown) {
        clearInterval(progressInterval);
        setProgress(0);
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (detail === 'Student not found') {
          localStorage.removeItem('lastStudentId');
          setError('Session expired — the server restarted. Please resubmit your form.');
        } else {
          // runMatch timed out or errored — check if partial results are already in DB
          try {
            const partial = await getMatches(Number(studentId));
            if (partial.length > 0) {
              setMatches(partial as MatchWithPI[]);
              // Show results silently — no error banner
              return;
            }
          } catch {
            // getMatches also failed — fall through to error
          }
          setError(detail ?? (status ? `Server error ${status} — click Retry.` : 'Could not load matches — click Retry.'));
        }
      }
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
            <div className="text-center w-72">
              <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-500 text-sm mb-3">{matchingStatus}</p>
              {progress > 0 && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-violet-600 h-2 rounded-full transition-all duration-200"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-6">
            <p>{error}</p>
            <div className="flex gap-3 mt-3">
              {error.includes('resubmit') || error.includes('expired') ? (
                <Link to="/" className="font-medium underline">← Back to form</Link>
              ) : (
                <button
                  onClick={loadOrRun}
                  className="bg-red-100 hover:bg-red-200 text-red-800 font-medium px-4 py-1.5 rounded-lg text-sm transition-colors"
                >
                  Retry
                </button>
              )}
            </div>
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
