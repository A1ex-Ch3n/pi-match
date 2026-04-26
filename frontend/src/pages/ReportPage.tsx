import { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getReport } from '../api/client';
import type { ChemistryReport, MatchResult } from '../types';
import ScoreRadar, { chemistryRadarDimensions } from '../components/ScoreRadar';
import { DEMO_REPORT, getDemoMatch } from '../data/mockChat';

const DIMENSION_LABELS: Record<keyof ChemistryReport['dimension_scores'], string> = {
  research_alignment: 'Research alignment',
  mentorship_compatibility: 'Mentorship compatibility',
  culture_fit: 'Culture fit',
  communication_fit: 'Communication',
  red_flags: 'No red flags',
};

const DIMENSION_ORDER: (keyof ChemistryReport['dimension_scores'])[] = [
  'research_alignment',
  'mentorship_compatibility',
  'culture_fit',
  'communication_fit',
  'red_flags',
];

export default function ReportPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const [searchParams] = useSearchParams();
  const isDemo = searchParams.get('demo') === '1';

  const [report, setReport] = useState<ChemistryReport | null>(null);
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isDemo) {
      setMatch(getDemoMatch(Number(matchId)));
      setReport(DEMO_REPORT);
      setLoading(false);
      return;
    }
    if (!matchId) return;
    getReport(Number(matchId))
      .then((data) => {
        setMatch(data.match);
        setReport(data.report);
      })
      .catch(() => setError('Could not load report.'))
      .finally(() => setLoading(false));
  }, [matchId, isDemo]);

  async function copyEmail() {
    if (!report?.pi_introduction_draft) return;
    await navigator.clipboard.writeText(report.pi_introduction_draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-ivory text-ink flex flex-col">
        <Nav isDemo={isDemo} matchId={matchId} />
        <main className="flex-1 flex items-center justify-center px-6">
          <div className="bg-bone border border-line rounded-2xl px-10 py-8 flex items-center gap-3">
            <Spinner />
            <span className="font-display text-lg text-ink">Reading your conversation…</span>
          </div>
        </main>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-ivory text-ink flex flex-col">
        <Nav isDemo={isDemo} matchId={matchId} />
        <main className="flex-1 flex items-center justify-center px-6">
          <div className="text-center max-w-md">
            <p className="font-display text-2xl text-ink mb-3">No chemistry report yet.</p>
            <p className="text-sm text-muted mb-7 leading-relaxed">
              Have a conversation with the PI avatar first — at least four exchanges —
              then the evaluator can read it and score the fit.
            </p>
            <Link
              to={`/chat/${matchId}${isDemo ? '?demo=1' : ''}`}
              className="inline-flex items-center gap-2 bg-forest text-ivory text-sm font-medium px-6 py-2.5 rounded-full hover:bg-forest-dark transition-colors shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)]"
            >
              ← Back to conversation
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const piName = match?.pi?.name ?? 'PI';
  const studentName = 'Demo Student'; // backend doesn't currently return student name on match
  const radarData = chemistryRadarDimensions(report.dimension_scores);
  const overall = Math.round(report.overall_score);

  return (
    <div className="min-h-screen bg-ivory text-ink flex flex-col">
      <Nav isDemo={isDemo} matchId={matchId} />

      <main className="flex-1 px-6 pt-12 pb-24">
        <div className="max-w-4xl mx-auto">
          {/* Editorial header */}
          <div className="mb-12">
            <p className="font-sans text-xs uppercase tracking-[0.18em] text-soft mb-3">
              Chemistry report
            </p>
            <h1 className="font-display font-light tracking-tight text-ink text-4xl md:text-6xl leading-[1.04]">
              {shortName(piName)} <span className="text-soft mx-2">×</span> {studentName}.
            </h1>
            <p className="mt-5 text-base md:text-lg text-muted italic max-w-2xl leading-relaxed">
              An independent evaluator read your conversation and scored five dimensions of fit.
            </p>
          </div>

          {/* Hero score + radar */}
          <HeroCard score={overall} radarData={radarData} />

          {/* Dimension breakdown */}
          <Section eyebrow="Dimension breakdown" title="Where the fit lands.">
            <div className="divide-y divide-line">
              {DIMENSION_ORDER.map((key) => (
                <DimensionRow
                  key={key}
                  label={DIMENSION_LABELS[key]}
                  score={report.dimension_scores[key]}
                  rationale={report.dimension_rationale[key]}
                />
              ))}
            </div>
          </Section>

          {/* Positives + Concerns */}
          <Section eyebrow="The signals" title="What's working, what to address.">
            <div className="grid md:grid-cols-2 gap-5">
              <PositivesCard items={report.key_positives} />
              <ConcernsCard items={report.key_concerns} />
            </div>
          </Section>

          {/* Recommended questions */}
          {report.recommended_questions.length > 0 && (
            <Section
              eyebrow="Bring these to the real conversation"
              title="Questions to ask in your first email or meeting."
            >
              <div className="bg-bone border border-line rounded-2xl p-7">
                <ol className="space-y-4">
                  {report.recommended_questions.map((q, i) => (
                    <li key={i} className="flex gap-4">
                      <span className="font-display tabular text-forest text-lg leading-none pt-0.5 shrink-0 w-6">
                        {i + 1}
                      </span>
                      <span className="text-sm text-ink leading-relaxed">
                        <Markdown>{q}</Markdown>
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            </Section>
          )}

          {/* Email draft */}
          <EmailCard
            email={report.pi_introduction_draft}
            piName={piName}
            piEmail={match?.pi?.email}
            copied={copied}
            onCopy={copyEmail}
          />
        </div>
      </main>
    </div>
  );
}

/* ───────────────────────── Nav ───────────────────────── */

function Nav({ isDemo, matchId }: { isDemo: boolean; matchId?: string }) {
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
        <Link
          to={`/chat/${matchId ?? ''}${isDemo ? '?demo=1' : ''}`}
          className="text-sm font-medium text-soft hover:text-ink transition-colors"
        >
          ← Conversation
        </Link>
      </div>
    </nav>
  );
}

/* ───────────────────────── Hero card ───────────────────────── */

function HeroCard({
  score,
  radarData,
}: {
  score: number;
  radarData: ReturnType<typeof chemistryRadarDimensions>;
}) {
  const scoreColor =
    score >= 70 ? 'text-forest' : score >= 50 ? 'text-gold' : 'text-clay';
  const label =
    score >= 80 ? 'Strong fit' : score >= 65 ? 'Solid fit' : score >= 50 ? 'Mixed fit' : 'Weak fit';
  const summary =
    score >= 80
      ? 'Strong technical alignment with one mentorship caveat worth addressing directly.'
      : score >= 65
      ? 'Workable fit overall — a few areas to clarify before committing.'
      : score >= 50
      ? 'Real overlap, but several open questions. Worth a second conversation.'
      : 'Limited overlap. Consider whether the gaps are addressable.';

  return (
    <div className="bg-bone border border-line rounded-3xl p-8 md:p-12 mb-16 shadow-[0_30px_70px_-30px_rgba(21,23,26,0.20)]">
      <div className="grid md:grid-cols-[1fr_1.1fr] gap-8 md:gap-12 items-center">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-soft mb-3">
            Overall chemistry
          </div>
          <div className={`font-display tabular font-light leading-none ${scoreColor} text-7xl md:text-8xl`}>
            {score}
          </div>
          <div className="mt-4 font-display text-xl text-ink">{label}</div>
          <p className="mt-3 text-sm md:text-base text-muted italic leading-relaxed max-w-sm">
            {summary}
          </p>
        </div>
        <div className="min-w-0">
          <ScoreRadar dimensions={radarData} height={320} />
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────── Section wrapper ───────────────────────── */

function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-16">
      <div className="mb-7">
        <p className="font-sans text-xs uppercase tracking-[0.18em] text-forest mb-2">
          {eyebrow}
        </p>
        <h2 className="font-display font-light tracking-tight text-ink text-2xl md:text-3xl leading-tight">
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

/* ───────────────────────── Dimension row ───────────────────────── */

function DimensionRow({
  label,
  score,
  rationale,
}: {
  label: string;
  score: number;
  rationale: string;
}) {
  const rounded = Math.round(score);
  const color = rounded >= 70 ? 'text-forest' : rounded >= 50 ? 'text-gold' : 'text-clay';
  const barColor = rounded >= 70 ? 'bg-forest' : rounded >= 50 ? 'bg-gold' : 'bg-clay';

  return (
    <div className="py-6 first:pt-0 last:pb-0">
      <div className="flex items-baseline justify-between mb-2">
        <div className="font-display text-base text-ink">{label}</div>
        <div className={`font-display tabular text-2xl ${color} leading-none`}>{rounded}</div>
      </div>
      <div className="h-1 rounded-full bg-line/70 overflow-hidden mb-3">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${rounded}%` }} />
      </div>
      <p className="text-sm text-muted leading-relaxed max-w-2xl">
        <Markdown>{rationale}</Markdown>
      </p>
    </div>
  );
}

/* ───────────────────────── Positives / Concerns ───────────────────────── */

function PositivesCard({ items }: { items: string[] }) {
  return (
    <div className="rounded-2xl bg-forest-soft/50 border border-forest/15 p-6">
      <div className="text-[11px] uppercase tracking-wider text-forest-dark mb-4 font-semibold">
        What's working
      </div>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5 text-sm text-ink leading-relaxed">
            <CheckIcon />
            <span>
              <Markdown>{item}</Markdown>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ConcernsCard({ items }: { items: string[] }) {
  return (
    <div className="rounded-2xl bg-gold-soft/60 border border-gold/20 p-6">
      <div className="text-[11px] uppercase tracking-wider text-gold mb-4 font-semibold">
        What to address
      </div>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5 text-sm text-ink leading-relaxed">
            <WarnIcon />
            <span>
              <Markdown>{item}</Markdown>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      className="mt-1 text-forest shrink-0"
      aria-hidden
    >
      <path
        d="M2 7.5l3 3 7-7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function WarnIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" className="mt-1 text-gold shrink-0" aria-hidden>
      <circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7 4v3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="7" cy="9.7" r="0.7" fill="currentColor" />
    </svg>
  );
}

/* ───────────────────────── Email card ───────────────────────── */

function EmailCard({
  email,
  piName,
  piEmail,
  copied,
  onCopy,
}: {
  email: string;
  piName: string;
  piEmail?: string;
  copied: boolean;
  onCopy: () => void;
}) {
  // Try to split out a "Subject:" line if present
  const lines = email.split('\n');
  let subject = `Prospective PhD applicant — ${shortName(piName)}`;
  let body = email;
  if (lines[0]?.toLowerCase().startsWith('subject:')) {
    subject = lines[0].replace(/^subject:\s*/i, '').trim();
    body = lines.slice(1).join('\n').replace(/^\n+/, '');
  }

  const mailto = `mailto:${piEmail ?? ''}?subject=${encodeURIComponent(
    subject,
  )}&body=${encodeURIComponent(body)}`;

  return (
    <section>
      <div className="mb-7">
        <p className="font-sans text-xs uppercase tracking-[0.18em] text-forest mb-2">
          Draft introduction email
        </p>
        <h2 className="font-display font-light tracking-tight text-ink text-2xl md:text-3xl leading-tight">
          For you to review and send.
        </h2>
      </div>

      <div className="bg-bone border border-line rounded-2xl overflow-hidden shadow-[0_24px_60px_-30px_rgba(21,23,26,0.20)]">
        {/* Email header */}
        <div className="px-7 py-5 border-b border-line/70 space-y-2.5">
          <Field label="To">{piEmail ?? `${shortName(piName).toLowerCase().replace(/\s+/g, '.')}@…`}</Field>
          <Field label="Subject">{subject}</Field>
        </div>

        {/* Email body */}
        <div className="px-7 py-7 bg-ivory/40">
          <div className="text-[15px] text-ink leading-[1.7] whitespace-pre-wrap max-w-2xl">
            {body}
          </div>
        </div>

        {/* Actions */}
        <div className="px-7 py-5 border-t border-line/70 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <p className="text-xs text-soft italic">
            PiMatch never sends. You always send the email yourself.
          </p>
          <div className="flex gap-2">
            <button
              onClick={onCopy}
              className="text-sm font-medium text-forest hover:text-forest-dark px-4 py-2 rounded-full border border-forest/30 hover:border-forest transition-colors"
            >
              {copied ? 'Copied' : 'Copy draft'}
            </button>
            <a
              href={mailto}
              className="inline-flex items-center gap-2 bg-forest text-ivory text-sm font-medium px-5 py-2 rounded-full hover:bg-forest-dark transition-colors shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)]"
            >
              Open in mail app
              <span aria-hidden>→</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-3 text-sm">
      <span className="text-[11px] uppercase tracking-wider text-soft w-16 shrink-0">{label}</span>
      <span className="text-ink truncate">{children}</span>
    </div>
  );
}

/* ───────────────────────── Markdown helper ───────────────────────── */

function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <span>{children}</span>,
        strong: ({ children }) => (
          <strong className="font-medium text-forest-dark">{children}</strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-forest underline decoration-forest/40 underline-offset-2 hover:decoration-forest"
          >
            {children}
          </a>
        ),
        code: ({ children }) => (
          <code className="bg-forest-soft text-forest-dark px-1 py-0.5 rounded text-xs font-mono">
            {children}
          </code>
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  );
}

/* ───────────────────────── Misc ───────────────────────── */

function Spinner() {
  return (
    <svg className="animate-spin text-forest" width="20" height="20" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function shortName(name: string): string {
  const parts = name.replace(/^Dr\.?\s+/, '').split(/\s+/);
  if (parts.length < 2) return name;
  return `Dr. ${parts[parts.length - 1]}`;
}
