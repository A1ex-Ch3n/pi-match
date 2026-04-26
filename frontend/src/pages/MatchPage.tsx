import { useEffect, useRef, useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { getMatches, runMatch } from '../api/client';
import type { MatchResult, PIProfile } from '../types';
import PICard from '../components/PICard';
import { MOCK_MATCHES } from '../data/mockMatches';

interface MatchWithPI extends MatchResult {
  pi: PIProfile;
}

const LOADING_MESSAGES = [
  'Reading recent papers from Caltech faculty…',
  'Comparing your background to PI abstracts…',
  'Cross-checking active NSF grants…',
  'Computing co-author connections…',
  'Estimating reply likelihood…',
  'Ranking matches by overall fit…',
];

export default function MatchPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === '1';
  const [matches, setMatches] = useState<MatchWithPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<'connecting' | 'loading' | 'scoring' | 'done'>('connecting');
  const [progress, setProgress] = useState(0);
  const [messageIdx, setMessageIdx] = useState(0);
  const [error, setError] = useState('');
  const messageTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isDemo) {
      setMatches(MOCK_MATCHES as MatchWithPI[]);
      setPhase('done');
      setLoading(false);
      return;
    }
    if (!studentId) return;
    loadOrRun();
    return () => {
      if (messageTimerRef.current) clearInterval(messageTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId, isDemo]);

  async function loadOrRun() {
    setLoading(true);
    setError('');
    setPhase('connecting');
    setProgress(0);

    const base = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace('/api', '');
    try {
      await Promise.race([
        fetch(`${base}/health`),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 40000)),
      ]);
    } catch {
      setLoading(false);
      setError(
        'Cannot reach the server. If running locally, start uvicorn first. On production, wait 30s and click Retry.'
      );
      return;
    }

    try {
      setPhase('loading');
      const existing = await getMatches(Number(studentId));
      if (existing.length > 0) {
        setMatches(existing as MatchWithPI[]);
        setPhase('done');
        setLoading(false);
        return;
      }

      setPhase('scoring');
      setProgress(0);
      setMessageIdx(0);

      const startTime = Date.now();
      const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        setProgress(Math.min(90, (elapsed / 20000) * 90));
      }, 200);

      messageTimerRef.current = setInterval(() => {
        setMessageIdx((i) => (i + 1) % LOADING_MESSAGES.length);
      }, 2400);

      try {
        const fresh = await runMatch(Number(studentId));
        clearInterval(progressInterval);
        if (messageTimerRef.current) clearInterval(messageTimerRef.current);
        setProgress(100);
        if (fresh.length === 0) localStorage.removeItem('lastStudentId');
        setMatches(fresh as MatchWithPI[]);
        setPhase('done');
      } catch (err: unknown) {
        clearInterval(progressInterval);
        if (messageTimerRef.current) clearInterval(messageTimerRef.current);
        setProgress(0);
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (detail === 'Student not found') {
          localStorage.removeItem('lastStudentId');
          setError('Session expired — the server restarted. Please resubmit your form.');
        } else {
          try {
            const partial = await getMatches(Number(studentId));
            if (partial.length > 0) {
              setMatches(partial as MatchWithPI[]);
              setPhase('done');
              return;
            }
          } catch {
            // fall through
          }
          setError(
            detail ??
              (status ? `Server error ${status} — click Retry.` : 'Could not load matches — click Retry.')
          );
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
    <div className="min-h-screen bg-ivory text-ink flex flex-col">
      <Nav isDemo={isDemo} />

      <main className="flex-1 px-6 pt-12 pb-24">
        <div className="max-w-3xl mx-auto">
          <Header count={sorted.length} loading={loading} />

          {loading && <LoadingState phase={phase} progress={progress} messageIdx={messageIdx} />}

          {error && <ErrorBanner error={error} onRetry={loadOrRun} />}

          {!loading && matches.length === 0 && !error && <EmptyState />}

          {!loading && sorted.length > 0 && (
            <div className="space-y-5">
              {sorted.map((match, i) => (
                <PICard
                  key={match.id ?? i}
                  match={match}
                  pi={match.pi}
                  rank={i + 1}
                  variant={i === 0 ? 'hero' : 'compact'}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

/* ───────────────────────── Sub-components ───────────────────────── */

function Nav({ isDemo }: { isDemo: boolean }) {
  return (
    <nav className="sticky top-0 z-50 bg-ivory/85 backdrop-blur border-b border-line/70">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-display text-lg font-medium tracking-tight text-ink">
            PiMatch
          </Link>
          {isDemo && (
            <span className="text-[10px] uppercase tracking-[0.14em] px-2 py-0.5 rounded-full bg-gold-soft text-gold border border-gold/20 font-semibold">
              Demo data
            </span>
          )}
        </div>
        <Link to="/survey" className="text-sm font-medium text-soft hover:text-ink transition-colors">
          ← New search
        </Link>
      </div>
    </nav>
  );
}

function Header({ count, loading }: { count: number; loading: boolean }) {
  return (
    <div className="mb-10">
      <p className="font-sans text-xs uppercase tracking-[0.18em] text-soft mb-3">Your matches</p>
      <h1 className="font-display font-light tracking-tight text-ink text-4xl md:text-5xl leading-[1.05]">
        {loading ? 'Finding your matches…' : 'Ranked by fit for you.'}
      </h1>
      {!loading && count > 0 && (
        <p className="mt-3 text-sm text-muted">
          {count} {count === 1 ? 'professor' : 'professors'} · sorted by overall score
        </p>
      )}
    </div>
  );
}

function LoadingState({
  phase,
  progress,
  messageIdx,
}: {
  phase: 'connecting' | 'loading' | 'scoring' | 'done';
  progress: number;
  messageIdx: number;
}) {
  const headline =
    phase === 'connecting'
      ? 'Connecting to server…'
      : phase === 'loading'
      ? 'Loading your matches…'
      : 'Scoring professors…';

  return (
    <div className="bg-bone border border-line rounded-2xl p-10">
      <div className="flex items-center gap-3 mb-6">
        <Spinner />
        <span className="font-display text-lg text-ink">{headline}</span>
      </div>

      {phase === 'scoring' && (
        <div
          key={messageIdx}
          className="step-enter text-sm text-muted mb-6 min-h-[1.25rem]"
        >
          {LOADING_MESSAGES[messageIdx]}
        </div>
      )}

      {phase === 'scoring' && (
        <div className="w-full bg-line/60 rounded-full h-1">
          <div
            className="bg-forest h-full rounded-full transition-[width] duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {phase !== 'scoring' && (
        <p className="text-sm text-soft">
          The first request after a quiet period can take ~30s while the server warms up.
        </p>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin text-forest" width="20" height="20" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function ErrorBanner({ error, onRetry }: { error: string; onRetry: () => void }) {
  const sessionExpired = error.includes('resubmit') || error.includes('expired');
  return (
    <div className="bg-clay-soft border border-clay/20 text-clay rounded-2xl px-5 py-4 text-sm mb-6">
      <p className="font-medium">{error}</p>
      <div className="flex gap-3 mt-3">
        {sessionExpired ? (
          <Link
            to="/survey"
            className="inline-flex items-center gap-1 font-medium text-clay hover:text-clay/70"
          >
            ← Back to form
          </Link>
        ) : (
          <button
            onClick={onRetry}
            className="bg-clay text-ivory text-xs font-medium px-4 py-1.5 rounded-full hover:bg-clay/80 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="bg-bone border border-line rounded-2xl py-16 px-8 text-center">
      <p className="font-display text-xl text-ink mb-2">No matches yet.</p>
      <p className="text-sm text-muted mb-6">
        Submit the survey to find PIs whose research aligns with yours.
      </p>
      <Link
        to="/survey"
        className="inline-flex items-center gap-2 bg-forest text-ivory text-sm font-medium px-6 py-2.5 rounded-full hover:bg-forest-dark transition-colors"
      >
        Start a new search
        <span aria-hidden>→</span>
      </Link>
    </div>
  );
}
