import { useState } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { MatchResult, PIProfile } from '../types';
import FlagBadge from './FlagBadge';

interface PICardProps {
  match: MatchResult;
  pi: PIProfile;
  rank: number;
  variant?: 'hero' | 'compact';
}

/* ───────────────────────── Helpers ───────────────────────── */

function scoreTier(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 65) return 'Strong';
  if (score >= 50) return 'Moderate';
  if (score >= 35) return 'Weak';
  return 'Poor';
}

function scoreColorBg(score: number): string {
  if (score >= 70) return 'bg-forest';
  if (score >= 50) return 'bg-gold';
  return 'bg-clay';
}

function scoreColorText(score: number): string {
  if (score >= 70) return 'text-forest';
  if (score >= 50) return 'text-gold';
  return 'text-clay';
}

function initials(name: string): string {
  const parts = name.replace(/^(Dr\.?|Prof\.?)\s+/i, '').trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function mentorshipRationale(score: number): string {
  if (score >= 80)
    return "Your independence, meeting frequency, and involvement preferences align closely with this PI's stated advising style.";
  if (score >= 60)
    return "Your mentorship preferences broadly match this PI's style, with some differences in autonomy or meeting cadence.";
  if (score >= 40)
    return 'There are notable gaps between your preferred advising style and what this PI typically offers.';
  return "Your mentorship expectations differ significantly from this PI's documented approach — worth discussing directly.";
}

function fundingRationale(score: number, pi: PIProfile): string {
  const parts: string[] = [];
  if (pi.has_active_nsf_grant) parts.push('Active NSF grant');
  if ((pi.total_active_funding_usd ?? 0) >= 500_000)
    parts.push(`$${((pi.total_active_funding_usd ?? 0) / 1000).toFixed(0)}K total funding`);
  else if ((pi.total_active_funding_usd ?? 0) > 0)
    parts.push(`$${((pi.total_active_funding_usd ?? 0) / 1000).toFixed(0)}K funding`);
  if (pi.is_recruiting) parts.push('actively recruiting');
  if (parts.length === 0)
    return 'No active NSF grant data found. Funding stability is uncertain — check their lab website.';
  return (
    parts.join(', ') +
    '. ' +
    (score >= 70 ? 'Funding outlook is strong.' : 'Some funding uncertainty — verify before applying.')
  );
}

function cultureRationale(score: number, pi: PIProfile): string {
  const size = pi.lab_size ?? 5;
  const sizeLabel = size <= 4 ? 'small' : size <= 12 ? 'medium' : 'large';
  if (score >= 70)
    return `Lab is ${sizeLabel} (${size} members). Culture and work-life balance alignment is strong.`;
  if (score >= 50)
    return `Lab is ${sizeLabel} (${size} members). Some mismatch with your size or work-life balance preference.`;
  return `Lab is ${sizeLabel} (${size} members). Size or work-life balance expectations likely don't match your preference.`;
}

function skillsRationale(score: number): string {
  if (score >= 75) return "Strong overlap between your technical skills and the lab's research methods.";
  if (score >= 50)
    return "Partial skill overlap. Some of your technical background transfers; you'd need to develop new skills in the lab.";
  return 'Limited direct skill overlap detected. This could be a growth opportunity, or the technical gap may be significant.';
}

function buildScores(match: MatchResult, pi: PIProfile) {
  return [
    {
      key: 'research',
      label: 'Research direction',
      score: match.research_direction_score,
      weight: '40%',
      rationale: match.research_match_rationale || 'No research rationale available.',
    },
    {
      key: 'mentorship',
      label: 'Mentorship style',
      score: match.mentorship_style_score,
      weight: '20%',
      rationale: mentorshipRationale(match.mentorship_style_score),
    },
    {
      key: 'funding',
      label: 'Funding stability',
      score: match.funding_stability_score,
      weight: '15%',
      rationale: fundingRationale(match.funding_stability_score, pi),
    },
    {
      key: 'culture',
      label: 'Culture fit',
      score: match.culture_fit_score,
      weight: '10%',
      rationale: cultureRationale(match.culture_fit_score, pi),
    },
    {
      key: 'skills',
      label: 'Technical skills',
      score: match.technical_skills_score,
      weight: '10%',
      rationale: skillsRationale(match.technical_skills_score),
    },
  ];
}

/* ───────────────────────── Mini radar (fingerprint) ───────────────────────── */

function MiniRadar({ scores }: { scores: number[] }) {
  const cx = 50;
  const cy = 50;
  const R = 38;
  const angle = (i: number) => -Math.PI / 2 + (2 * Math.PI * i) / scores.length;

  const polyPoints = scores
    .map((s, i) => `${cx + Math.cos(angle(i)) * R * (s / 100)},${cy + Math.sin(angle(i)) * R * (s / 100)}`)
    .join(' ');

  return (
    <svg viewBox="0 0 100 100" className="w-24 h-24" aria-label="Match fingerprint">
      <polygon
        points={polyPoints}
        fill="var(--color-forest)"
        fillOpacity="0.22"
        stroke="var(--color-forest)"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ───────────────────────── Score row ───────────────────────── */

function ScoreRow({
  label,
  score,
  weight,
  rationale,
  isExpanded,
  onToggle,
  alwaysExpanded = false,
}: {
  label: string;
  score: number;
  weight: string;
  rationale: string;
  isExpanded: boolean;
  onToggle: () => void;
  alwaysExpanded?: boolean;
}) {
  const expanded = alwaysExpanded || isExpanded;
  return (
    <div className="border-b border-line/50 last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        disabled={alwaysExpanded}
        className="w-full flex items-center gap-3 py-2.5 text-left hover:bg-forest-soft/30 disabled:hover:bg-transparent rounded-md px-2 -mx-2 transition-colors"
      >
        <span className="w-36 text-xs text-muted shrink-0">{label}</span>
        <div className="flex-1 bg-line/60 rounded-full h-1.5 overflow-hidden">
          <div
            className={`${scoreColorBg(score)} h-full rounded-full transition-all`}
            style={{ width: `${score}%` }}
          />
        </div>
        <span className="font-display tabular text-sm text-ink w-8 text-right">{score.toFixed(0)}</span>
        <span className="text-[11px] text-soft w-10 text-right tabular">{weight}</span>
        {!alwaysExpanded && (
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            className={`text-soft transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          >
            <path
              d="M2 3.5l3 3 3-3"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>
      {expanded && (
        <div className="px-2 pb-3 pt-1">
          <div className={`text-xs font-medium mb-1 ${scoreColorText(score)}`}>
            {scoreTier(score)} match
          </div>
          <div className="text-sm text-muted leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                strong: ({ children }) => (
                  <strong className="font-semibold text-ink">{children}</strong>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-forest underline hover:text-forest-dark"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {rationale}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── Common bits ───────────────────────── */

function Avatar({ name, size = 'md' }: { name: string; size?: 'md' | 'lg' }) {
  const cls = size === 'lg' ? 'w-14 h-14 text-lg' : 'w-11 h-11 text-base';
  return (
    <div
      className={`${cls} rounded-full bg-forest text-ivory font-display font-medium tracking-wide flex items-center justify-center shrink-0`}
    >
      {initials(name)}
    </div>
  );
}

function ReplyChip({ likelihood }: { likelihood: 'high' | 'medium' | 'low' }) {
  const dot = likelihood === 'high' ? 'bg-forest' : likelihood === 'medium' ? 'bg-gold' : 'bg-clay';
  const labels = { high: 'High reply likelihood', medium: 'Medium reply likelihood', low: 'Low reply likelihood' };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted">
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {labels[likelihood]}
    </span>
  );
}

function FlagsRow({ match, pi }: { match: MatchResult; pi: PIProfile }) {
  const hasFlags =
    match.is_direct_connection ||
    match.is_indirect_connection ||
    match.citizenship_mismatch ||
    pi.has_active_nsf_grant;
  if (!hasFlags) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {match.is_direct_connection && <FlagBadge type="direct" />}
      {match.is_indirect_connection && (
        <FlagBadge type="indirect" via={match.indirect_connection_via} />
      )}
      {match.citizenship_mismatch && <FlagBadge type="citizenship" />}
      {pi.has_active_nsf_grant && <FlagBadge type="funding" />}
    </div>
  );
}

function ResearchAreas({ areas, max = 4 }: { areas: string[]; max?: number }) {
  const list = (areas ?? []).slice(0, max);
  if (list.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {list.map((area) => (
        <span
          key={area}
          className="text-xs px-2.5 py-1 rounded-full bg-forest-soft text-forest-dark font-medium"
        >
          {area}
        </span>
      ))}
    </div>
  );
}

function PrimaryActions({
  match,
  piName,
  variant,
}: {
  match: MatchResult;
  piName: string;
  variant: 'hero' | 'compact';
}) {
  if (match.id == null || isNaN(match.id)) return null;
  const heroBtn =
    'inline-flex items-center justify-center gap-2 bg-forest text-ivory text-sm font-medium px-5 py-2.5 rounded-full hover:bg-forest-dark transition-colors shadow-[0_8px_20px_-10px_rgba(47,74,58,0.45)]';
  const subBtn =
    'inline-flex items-center justify-center gap-2 bg-bone border border-line text-ink text-sm font-medium px-5 py-2.5 rounded-full hover:border-forest/40 transition-colors';
  const firstName = piName.replace(/^(Dr\.?|Prof\.?)\s+/i, '').split(/\s+/).slice(-1)[0];
  return (
    <div className={`flex flex-wrap gap-2 ${variant === 'hero' ? '' : 'justify-end'}`}>
      <Link to={`/chat/${match.id}`} className={heroBtn}>
        Talk with Dr. {firstName} <span aria-hidden>→</span>
      </Link>
      {match.transcript && match.transcript.length > 0 && (
        <Link to={`/report/${match.id}`} className={subBtn}>
          View report
        </Link>
      )}
    </div>
  );
}

/* ───────────────────────── Main card (variant aware) ───────────────────────── */

export default function PICard({ match, pi, rank, variant = 'compact' }: PICardProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const toggle = (key: string) => setExpanded((prev) => (prev === key ? null : key));
  const scores = buildScores(match, pi);
  const radarScores = scores.map((s) => s.score);

  if (variant === 'hero') {
    return (
      <article className="bg-bone rounded-3xl border border-line shadow-[0_30px_70px_-30px_rgba(21,23,26,0.18)] overflow-hidden">
        <div className="px-7 pt-6 pb-5 border-b border-line/60 flex items-center justify-between">
          <span className="font-sans text-[11px] uppercase tracking-[0.18em] text-forest font-semibold">
            Top match
          </span>
          {pi.lab_website && (
            <a
              href={pi.lab_website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-soft hover:text-ink"
            >
              Lab website ↗
            </a>
          )}
        </div>

        <div className="px-7 py-7">
          <div className="flex items-start gap-5">
            <Avatar name={pi.name} size="lg" />
            <div className="flex-1 min-w-0">
              <h2 className="font-display font-light text-3xl md:text-4xl text-ink leading-tight tracking-tight">
                {pi.name}
              </h2>
              <p className="text-sm text-muted mt-1">
                {pi.department} · {pi.institution}
              </p>
            </div>
            <div className="text-right shrink-0">
              <div className="font-display tabular text-6xl text-forest leading-none">
                {match.overall_score.toFixed(0)}
              </div>
              <div className="text-xs text-soft mt-1 tracking-wider">/ 100</div>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            <FlagsRow match={match} pi={pi} />
            <ResearchAreas areas={pi.research_areas} />
          </div>

          <div className="mt-7 flex flex-col md:flex-row gap-6 items-start">
            <div className="shrink-0">
              <MiniRadar scores={radarScores} />
              <p className="text-[10px] uppercase tracking-wider text-soft mt-1 text-center">
                Match fingerprint
              </p>
            </div>
            <div className="flex-1">
              <p className="text-[11px] uppercase tracking-wider text-forest font-semibold mb-2">
                Why this is your top match
              </p>
              <div className="text-base text-ink leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    strong: ({ children }) => (
                      <strong className="font-semibold">{children}</strong>
                    ),
                  }}
                >
                  {match.research_match_rationale || 'No rationale available.'}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          <div className="mt-7 pt-5 border-t border-line/60">
            <p className="text-[11px] uppercase tracking-wider text-soft mb-2">Score breakdown</p>
            <div>
              {scores.map(({ key, label, score, weight, rationale }) => (
                <ScoreRow
                  key={key}
                  label={label}
                  score={score}
                  weight={weight}
                  rationale={rationale}
                  isExpanded={expanded === key}
                  onToggle={() => toggle(key)}
                  alwaysExpanded={false}
                />
              ))}
            </div>
            <p className="text-[11px] text-soft mt-3">Click any dimension to see the rationale.</p>
          </div>

          <div className="mt-7 flex items-center justify-between gap-4 flex-wrap">
            <ReplyChip likelihood={match.reply_likelihood} />
            <PrimaryActions match={match} piName={pi.name} variant="hero" />
          </div>
        </div>
        <div className="absolute -z-10">{rank}</div>
      </article>
    );
  }

  // ───────── Compact card ─────────
  return (
    <article className="bg-bone rounded-2xl border border-line p-6 hover:border-forest/30 transition-colors">
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-center shrink-0">
          <span className="font-display tabular text-xs text-soft mb-1">#{rank}</span>
          <Avatar name={pi.name} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="min-w-0">
              <h3 className="font-display text-xl text-ink leading-tight font-normal">{pi.name}</h3>
              <p className="text-xs text-muted mt-0.5 truncate">
                {pi.department} · {pi.institution}
              </p>
            </div>
            <div className="text-right shrink-0">
              <div className="font-display tabular text-3xl text-forest leading-none">
                {match.overall_score.toFixed(0)}
              </div>
              <div className="text-[10px] text-soft tracking-wider mt-0.5">/ 100</div>
            </div>
          </div>

          <div className="space-y-2">
            <FlagsRow match={match} pi={pi} />
            <ResearchAreas areas={pi.research_areas} max={4} />
          </div>

          <div className="mt-4">
            {scores.map(({ key, label, score, weight, rationale }) => (
              <ScoreRow
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

          <div className="mt-4 flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-4">
              <ReplyChip likelihood={match.reply_likelihood} />
              {pi.lab_website && (
                <a
                  href={pi.lab_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-soft hover:text-ink"
                >
                  Lab website ↗
                </a>
              )}
            </div>
            <PrimaryActions match={match} piName={pi.name} variant="compact" />
          </div>
        </div>
      </div>
    </article>
  );
}
