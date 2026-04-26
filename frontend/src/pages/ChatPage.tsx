import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { simulate, evaluate, getMatch, type SimulateResponse } from '../api/client';
import type { MatchResult, PIProfile, TranscriptMessage } from '../types';
import ChatBubble from '../components/ChatBubble';
import FlagBadge from '../components/FlagBadge';
import { DEMO_TRANSCRIPT, DEMO_SUGGESTED_OPENERS, getDemoMatch } from '../data/mockChat';

export default function ChatPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === '1';
  const navigate = useNavigate();

  const [match, setMatch] = useState<MatchResult | null>(null);
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isDemo) {
      const demo = getDemoMatch(Number(matchId));
      setMatch(demo);
      setMessages([]);
      setLoading(false);
      return;
    }
    if (!matchId || isNaN(Number(matchId))) {
      navigate('/', { replace: true });
      return;
    }
    loadMatch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId, isDemo]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  // Autosize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  }, [input]);

  async function loadMatch() {
    try {
      const data = await getMatch(Number(matchId));
      setMatch(data);
      if (data.transcript && data.transcript.length > 0) setMessages(data.transcript);
    } catch {
      setError('Could not load conversation. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(textOverride?: string) {
    const text = (textOverride ?? input).trim();
    if (!text || sending) return;
    const userMessage: TranscriptMessage = { role: 'student', content: text };
    setError('');

    if (isDemo) {
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setSending(true);
      const piCount = messages.filter((m) => m.role === 'pi').length;
      const piTurns = DEMO_TRANSCRIPT.filter((m) => m.role === 'pi');
      const nextPi = piTurns[piCount];
      setTimeout(() => {
        if (nextPi) setMessages((prev) => [...prev, nextPi]);
        setSending(false);
      }, 900);
      return;
    }

    if (!matchId) return;
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSending(true);
    try {
      const updated: SimulateResponse = await simulate(Number(matchId), text);
      if (updated.transcript) setMessages(updated.transcript);
    } catch {
      setError('Failed to send message. Check that the backend is running.');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  function handleOpener(text: string) {
    handleSend(text);
  }

  async function handleEvaluate() {
    if (isDemo) {
      navigate(`/report/${matchId}?demo=1`);
      return;
    }
    if (!matchId) return;
    setEvaluating(true);
    setError('');
    try {
      await evaluate(Number(matchId));
      navigate(`/report/${matchId}`);
    } catch {
      setError('Evaluation failed. Make sure you have a conversation first.');
      setEvaluating(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const piName = match?.pi?.name ?? 'PI Avatar';
  const piInitials = piName
    .replace(/^Dr\.?\s+/, '')
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();
  const canEvaluate = messages.length >= 4;

  return (
    <div className="min-h-screen bg-ivory text-ink flex flex-col">
      <Nav
        isDemo={isDemo}
        studentId={match?.student_id}
        onEvaluate={handleEvaluate}
        canEvaluate={canEvaluate}
        evaluating={evaluating}
      />

      <main className="flex-1 px-6 pt-12 pb-32">
        <div className="max-w-6xl mx-auto">
          {/* Page header */}
          <div className="mb-10">
            <p className="font-sans text-xs uppercase tracking-[0.18em] text-soft mb-3">
              Conversation
            </p>
            <h1 className="font-display font-light tracking-tight text-ink text-3xl md:text-5xl leading-[1.05]">
              {loading ? 'Loading…' : `A conversation with ${shortName(piName)}.`}
            </h1>
          </div>

          {loading ? (
            <LoadingState />
          ) : (
            <div className="grid md:grid-cols-[320px_1fr] gap-10 lg:gap-14">
              {/* Sidebar dossier */}
              {match?.pi && (
                <aside className="md:sticky md:top-24 md:self-start">
                  <Dossier match={match} pi={match.pi} initials={piInitials} />
                </aside>
              )}

              {/* Transcript + composer */}
              <div className="min-w-0">
                {error && (
                  <div className="mb-5 bg-clay-soft border border-clay/20 text-clay rounded-2xl px-5 py-3 text-sm">
                    {error}
                  </div>
                )}

                {messages.length === 0 ? (
                  <EmptyState
                    piName={shortName(piName)}
                    openers={isDemo ? DEMO_SUGGESTED_OPENERS : defaultOpeners(match?.pi)}
                    onPick={handleOpener}
                  />
                ) : (
                  <div>
                    {messages.map((msg, i) => (
                      <ChatBubble key={i} message={msg} piInitials={piInitials} />
                    ))}
                    {sending && <TypingIndicator initials={piInitials} />}
                    <div ref={bottomRef} />

                    {canEvaluate && !sending && (
                      <FinalCTA onEvaluate={handleEvaluate} evaluating={evaluating} />
                    )}
                  </div>
                )}

                <Composer
                  value={input}
                  onChange={setInput}
                  onSend={() => handleSend()}
                  onKeyDown={handleKeyDown}
                  disabled={sending}
                  textareaRef={textareaRef}
                  piName={shortName(piName)}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

/* ───────────────────────── Nav ───────────────────────── */

function Nav({
  isDemo,
  studentId,
  onEvaluate,
  canEvaluate,
  evaluating,
}: {
  isDemo: boolean;
  studentId?: number;
  onEvaluate: () => void;
  canEvaluate: boolean;
  evaluating: boolean;
}) {
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
        <div className="flex items-center gap-5">
          <Link
            to={`/matches/${studentId ?? ''}${isDemo ? '?demo=1' : ''}`}
            className="text-sm font-medium text-soft hover:text-ink transition-colors"
          >
            ← Matches
          </Link>
          <button
            onClick={onEvaluate}
            disabled={!canEvaluate || evaluating}
            className="text-sm font-medium text-forest hover:text-forest-dark disabled:text-soft disabled:cursor-not-allowed transition-colors"
          >
            {evaluating ? 'Evaluating…' : 'Get chemistry report →'}
          </button>
        </div>
      </div>
    </nav>
  );
}

/* ───────────────────────── Dossier (sidebar) ───────────────────────── */

function Dossier({
  match,
  pi,
  initials,
}: {
  match: MatchResult;
  pi: PIProfile;
  initials: string;
}) {
  const score = Math.round(match.overall_score);
  const scoreColor =
    score >= 70 ? 'text-forest' : score >= 50 ? 'text-gold' : 'text-clay';

  return (
    <div className="rounded-2xl bg-bone border border-line p-6 shadow-[0_18px_40px_-22px_rgba(21,23,26,0.18)]">
      {/* Identity */}
      <div className="flex items-start gap-3">
        <div className="w-14 h-14 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-lg font-medium tracking-wide shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <div className="font-display text-base text-ink leading-tight">{pi.name}</div>
          <div className="text-xs text-soft mt-1 leading-snug">
            {pi.department}
            <br />
            {pi.institution}
          </div>
        </div>
      </div>

      {/* Score + rationale */}
      <div className="mt-5 pt-5 border-t border-line">
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-[11px] uppercase tracking-wider text-soft">Match score</div>
          <div className={`font-display tabular text-3xl leading-none ${scoreColor}`}>
            {score}
          </div>
        </div>
        {match.research_match_rationale && (
          <p className="text-xs text-muted leading-relaxed mt-2 line-clamp-3">
            {stripMd(match.research_match_rationale)}
          </p>
        )}
      </div>

      {/* Mini radar fingerprint */}
      <div className="mt-5 pt-5 border-t border-line">
        <div className="text-[11px] uppercase tracking-wider text-soft mb-2">Fit fingerprint</div>
        <MiniRadar
          scores={[
            match.research_direction_score,
            match.mentorship_style_score,
            match.funding_stability_score,
            match.culture_fit_score,
            match.technical_skills_score,
          ]}
        />
      </div>

      {/* Research areas */}
      {pi.research_areas.length > 0 && (
        <div className="mt-5 pt-5 border-t border-line">
          <div className="text-[11px] uppercase tracking-wider text-soft mb-2">Research areas</div>
          <div className="flex flex-wrap gap-1.5">
            {pi.research_areas.slice(0, 4).map((a) => (
              <span
                key={a}
                className="text-[11px] px-2 py-0.5 rounded-full bg-forest-soft text-forest-dark font-medium"
              >
                {a}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Funding */}
      <div className="mt-5 pt-5 border-t border-line">
        <div className="text-[11px] uppercase tracking-wider text-soft mb-2">Funding</div>
        <p className="text-xs text-ink leading-relaxed">
          {fundingLine(pi)}
        </p>
      </div>

      {/* Flags */}
      {(match.is_direct_connection ||
        match.is_indirect_connection ||
        match.citizenship_mismatch ||
        pi.has_active_nsf_grant) && (
        <div className="mt-5 pt-5 border-t border-line">
          <div className="flex flex-wrap gap-1.5">
            {match.is_direct_connection && <FlagBadge type="direct" />}
            {match.is_indirect_connection && (
              <FlagBadge type="indirect" via={match.indirect_connection_via} />
            )}
            {match.citizenship_mismatch && <FlagBadge type="citizenship" />}
            {pi.has_active_nsf_grant && !match.citizenship_mismatch && (
              <FlagBadge type="funding" />
            )}
          </div>
        </div>
      )}

      {/* Disclosure */}
      <div className="mt-5 pt-5 border-t border-line">
        <p className="text-[11px] text-soft italic leading-relaxed">
          Avatar built from her own survey responses and anonymous answers from current lab
          members. When uncertain, she'll say so.
        </p>
      </div>
    </div>
  );
}

const RADAR_LABELS = ['Research', 'Mentorship', 'Funding', 'Culture', 'Skills'];

function MiniRadar({ scores }: { scores: number[] }) {
  const cx = 80;
  const cy = 80;
  const R = 45;
  const labelR = R + 18;
  const angle = (i: number) => -Math.PI / 2 + (2 * Math.PI * i) / scores.length;

  const polyPoints = scores
    .map((s, i) => {
      const r = (Math.max(0, Math.min(100, s)) / 100) * R;
      return `${cx + Math.cos(angle(i)) * r},${cy + Math.sin(angle(i)) * r}`;
    })
    .join(' ');

  const grid = [0.4, 0.7, 1.0].map((scale) =>
    scores
      .map(
        (_, i) => `${cx + Math.cos(angle(i)) * R * scale},${cy + Math.sin(angle(i)) * R * scale}`,
      )
      .join(' '),
  );

  return (
    <svg viewBox="0 0 160 160" className="w-full h-40">
      {grid.map((g, i) => (
        <polygon key={i} points={g} fill="none" stroke="var(--color-line)" strokeWidth="1" />
      ))}
      {scores.map((_, i) => (
        <line
          key={i}
          x1={cx}
          y1={cy}
          x2={cx + Math.cos(angle(i)) * R}
          y2={cy + Math.sin(angle(i)) * R}
          stroke="var(--color-line)"
          strokeWidth="1"
        />
      ))}
      <polygon
        points={polyPoints}
        fill="var(--color-forest)"
        fillOpacity="0.2"
        stroke="var(--color-forest)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      {scores.map((_, i) => {
        const a = angle(i);
        const lx = cx + Math.cos(a) * labelR;
        const ly = cy + Math.sin(a) * labelR;
        const anchor = Math.cos(a) > 0.3 ? 'start' : Math.cos(a) < -0.3 ? 'end' : 'middle';
        return (
          <text
            key={i}
            x={lx}
            y={ly}
            textAnchor={anchor}
            dominantBaseline="middle"
            fontSize="9"
            fill="var(--color-muted, #6b7280)"
            fontFamily="sans-serif"
          >
            {RADAR_LABELS[i]}
          </text>
        );
      })}
    </svg>
  );
}

/* ───────────────────────── Empty state ───────────────────────── */

function EmptyState({
  piName,
  openers,
  onPick,
}: {
  piName: string;
  openers: string[];
  onPick: (t: string) => void;
}) {
  return (
    <div className="mb-8">
      <p className="text-sm text-muted leading-relaxed mb-5">
        {piName}'s avatar is ready when you are. Ask anything — research direction, lab
        culture, funding, or how she actually runs her group. Or start with one of these:
      </p>
      <div className="space-y-2">
        {openers.map((o) => (
          <button
            key={o}
            onClick={() => onPick(o)}
            className="block w-full text-left px-4 py-3 rounded-2xl bg-bone border border-line text-sm text-ink hover:border-forest/40 hover:bg-forest-soft/30 transition-colors group"
          >
            <span className="text-soft group-hover:text-forest transition-colors mr-2">›</span>
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ───────────────────────── Typing indicator ───────────────────────── */

function TypingIndicator({ initials }: { initials: string }) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="w-9 h-9 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-sm font-medium shrink-0">
        {initials}
      </div>
      <div className="rounded-2xl rounded-tl-sm bg-bone border border-line px-4 py-3 shadow-[0_8px_24px_-12px_rgba(21,23,26,0.12)]">
        <div className="flex gap-1.5 items-center h-5">
          <span
            className="w-1.5 h-1.5 bg-forest/60 rounded-full animate-pulse"
            style={{ animationDelay: '0ms', animationDuration: '1200ms' }}
          />
          <span
            className="w-1.5 h-1.5 bg-forest/60 rounded-full animate-pulse"
            style={{ animationDelay: '200ms', animationDuration: '1200ms' }}
          />
          <span
            className="w-1.5 h-1.5 bg-forest/60 rounded-full animate-pulse"
            style={{ animationDelay: '400ms', animationDuration: '1200ms' }}
          />
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────── Final CTA ───────────────────────── */

function FinalCTA({ onEvaluate, evaluating }: { onEvaluate: () => void; evaluating: boolean }) {
  return (
    <div className="mt-10 mb-4 rounded-2xl border border-forest/20 bg-forest-soft/40 p-6 text-center">
      <p className="font-display text-lg text-ink mb-1">Done talking?</p>
      <p className="text-sm text-muted mb-5">
        A fresh evaluator will read this transcript and score five dimensions of fit.
      </p>
      <button
        onClick={onEvaluate}
        disabled={evaluating}
        className="inline-flex items-center gap-2 bg-forest text-ivory text-sm font-medium px-6 py-2.5 rounded-full hover:bg-forest-dark disabled:opacity-60 transition-colors shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)]"
      >
        {evaluating ? 'Evaluating…' : 'Get your chemistry report'}
        <span aria-hidden>→</span>
      </button>
    </div>
  );
}

/* ───────────────────────── Composer ───────────────────────── */

function Composer({
  value,
  onChange,
  onSend,
  onKeyDown,
  disabled,
  textareaRef,
  piName,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  disabled: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  piName: string;
}) {
  return (
    <div className="mt-6">
      <div className="flex items-end gap-2 rounded-2xl bg-bone border border-line focus-within:border-forest/40 focus-within:ring-2 focus-within:ring-forest/15 transition-all p-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={`Message ${piName}…`}
          className="flex-1 bg-transparent px-3 py-2 text-sm text-ink placeholder:text-soft resize-none focus:outline-none leading-relaxed"
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          aria-label="Send"
          className="shrink-0 w-10 h-10 rounded-full bg-forest text-ivory flex items-center justify-center hover:bg-forest-dark disabled:bg-line disabled:text-soft disabled:cursor-not-allowed transition-colors shadow-[0_6px_18px_-8px_rgba(47,74,58,0.5)]"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M3 8h10M9 4l4 4-4 4"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
      <p className="text-[11px] text-soft text-center mt-2 italic">
        AI avatar of {piName} — when she's unsure, she'll say so. Press Enter to send,
        Shift+Enter for newline.
      </p>
    </div>
  );
}

/* ───────────────────────── Loading ───────────────────────── */

function LoadingState() {
  return (
    <div className="bg-bone border border-line rounded-2xl p-10 flex items-center gap-3">
      <svg
        className="animate-spin text-forest"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
        <path
          d="M22 12a10 10 0 0 0-10-10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      <span className="font-display text-lg text-ink">Loading conversation…</span>
    </div>
  );
}

/* ───────────────────────── Helpers ───────────────────────── */

function shortName(name: string): string {
  // "Dr. Karen Liu" → "Dr. Liu"
  const parts = name.replace(/^Dr\.?\s+/, '').split(/\s+/);
  if (parts.length < 2) return name;
  return `Dr. ${parts[parts.length - 1]}`;
}

function stripMd(s: string): string {
  return s.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1');
}

function fundingLine(pi: PIProfile): string {
  if (pi.has_active_nsf_grant && pi.total_active_funding_usd) {
    const usd = `$${(pi.total_active_funding_usd / 1_000_000).toFixed(2)}M`;
    return pi.funding_citizen_restricted
      ? `Active NSF grant · ${usd} (citizen-restricted)`
      : `Active NSF grant · ${usd} active`;
  }
  if (pi.total_active_funding_usd && pi.total_active_funding_usd > 0) {
    return `$${(pi.total_active_funding_usd / 1_000_000).toFixed(2)}M active funding`;
  }
  return 'Funding details unavailable.';
}

function defaultOpeners(pi?: PIProfile): string[] {
  const area = pi?.research_areas?.[0] ?? 'your research';
  return [
    `Tell me about your recent work in ${area}.`,
    "What's your lab's typical meeting cadence?",
    'How does funding work for new students in your group?',
  ];
}
