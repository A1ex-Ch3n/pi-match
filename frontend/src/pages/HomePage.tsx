import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-ivory text-ink">
      <Nav />
      <Hero />
      <Feature
        eyebrow="The match"
        headline="Match on what actually matters."
        body="PiMatch reads your background and the PI's last three years of papers, then explains the overlap in their actual words — not generic keywords."
        visual={<ResearchFitVisual />}
        align="right"
      />
      <Feature
        eyebrow="The conversation"
        headline="Talk to your PI before you talk to your PI."
        body="An AI avatar built from the PI's own survey answers and their current students' anonymous responses. It speaks specifically. When it doesn't know, it says so."
        visual={<ChatVisual />}
        align="left"
      />
      <Feature
        eyebrow="The report"
        headline="Walk in with a chemistry report."
        body="After the conversation, a fresh evaluator scores five dimensions of fit, surfaces concerns to address, and drafts an introduction email — for you to review and send."
        visual={<ReportVisual />}
        align="right"
      />
      <FinalCTA />
      <Footer />
    </div>
  );
}

/* ───────────────────────── Nav ───────────────────────── */

function Nav() {
  return (
    <nav className="sticky top-0 z-50 bg-ivory/85 backdrop-blur border-b border-line/70">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="font-display text-lg font-medium tracking-tight text-ink">
          PiMatch
        </Link>
        <Link
          to="/survey"
          className="text-sm font-medium text-ink hover:text-forest transition-colors"
        >
          Start <span aria-hidden>→</span>
        </Link>
      </div>
    </nav>
  );
}

/* ───────────────────────── Hero ───────────────────────── */

function Hero() {
  return (
    <section className="px-6 pt-20 pb-24 md:pt-28 md:pb-32">
      <div className="max-w-5xl mx-auto text-center">
        <p className="font-sans text-xs uppercase tracking-[0.18em] text-soft mb-6">
          PhD advisor matchmaking
        </p>
        <h1 className="font-display font-light tracking-tight text-ink text-5xl md:text-7xl leading-[1.04]">
          Find the PhD advisor
          <br />
          who truly aligns with
          <br />
          your research goals.
        </h1>
        <p className="mt-8 mx-auto max-w-2xl text-lg md:text-xl text-muted leading-relaxed">
          PiMatch reads every paper, every grant, every word your future PI has written —
          then runs a simulated conversation so you walk into the real one ready.
        </p>
        <div className="mt-10 flex flex-col items-center">
          <Link
            to="/survey"
            className="inline-flex items-center gap-2 bg-forest text-ivory text-base font-medium px-8 py-3.5 rounded-full hover:bg-forest-dark transition-colors shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)]"
          >
            Start your match
            <span aria-hidden>→</span>
          </Link>
          <p className="mt-3 text-sm text-soft">Takes about 5 minutes</p>
        </div>
      </div>

      <HeroComposition />
    </section>
  );
}

function HeroComposition() {
  return (
    <div className="mt-20 md:mt-24 max-w-5xl mx-auto px-2">
      <div className="relative h-[440px] md:h-[480px]">
        {/* Back card — left */}
        <div className="absolute left-2 md:left-8 top-8 w-72 -rotate-[7deg] opacity-95">
          <PICardMock
            initials="AB"
            name="Dr. Aisha Brown"
            dept="Caltech · Bioengineering"
            score={81}
            tags={['Protein Design', 'Cryo-EM']}
            tone="muted"
          />
        </div>

        {/* Back card — right */}
        <div className="absolute right-2 md:right-8 top-12 w-72 rotate-[6deg] opacity-95">
          <PICardMock
            initials="MR"
            name="Dr. Manish Rao"
            dept="Caltech · Computing & Math Sci"
            score={87}
            tags={['Reinforcement Learning', 'Robotics']}
            tone="muted"
          />
        </div>

        {/* Mid card — slightly behind report */}
        <div className="absolute left-1/2 -translate-x-1/2 top-2 w-72 -rotate-[2deg]">
          <PICardMock
            initials="KL"
            name="Dr. Karen Liu"
            dept="Caltech · Computational Bio"
            score={92}
            tags={['Generative Models', 'Genomics', 'Diffusion']}
            tone="emphasis"
          />
        </div>

        {/* Front: Chemistry Report */}
        <div className="absolute left-1/2 -translate-x-1/2 bottom-0 w-[20rem] md:w-[22rem] rotate-[1.5deg]">
          <ReportCardMock />
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────── Mock cards ───────────────────────── */

function PICardMock({
  initials,
  name,
  dept,
  score,
  tags,
  tone = 'muted',
}: {
  initials: string;
  name: string;
  dept: string;
  score: number;
  tags: string[];
  tone?: 'muted' | 'emphasis';
}) {
  const isEmph = tone === 'emphasis';
  return (
    <div
      className={`rounded-2xl bg-bone border border-line p-5 ${
        isEmph
          ? 'shadow-[0_30px_60px_-20px_rgba(21,23,26,0.22)]'
          : 'shadow-[0_18px_40px_-22px_rgba(21,23,26,0.20)]'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-base font-medium tracking-wide">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-ink text-sm leading-tight truncate">{name}</div>
          <div className="text-xs text-soft mt-0.5 truncate">{dept}</div>
        </div>
        <div className="font-display tabular text-3xl text-forest leading-none">{score}</div>
      </div>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {tags.map((t) => (
          <span
            key={t}
            className="text-[11px] px-2 py-0.5 rounded-full bg-forest-soft text-forest-dark font-medium"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function ReportCardMock() {
  return (
    <div className="rounded-2xl bg-bone border border-line p-6 shadow-[0_40px_80px_-20px_rgba(21,23,26,0.30)]">
      <div className="flex items-baseline justify-between">
        <div className="font-display text-sm text-muted tracking-tight">Chemistry Report</div>
        <div className="font-display tabular text-4xl text-ink leading-none">87</div>
      </div>
      <div className="mt-1 text-xs text-soft">Dr. Karen Liu</div>
      <div className="mt-3">
        <SmallRadar />
      </div>
      <div className="mt-3 space-y-1.5 text-[13px] leading-snug">
        <ReportLine icon="check">Strong research alignment</ReportLine>
        <ReportLine icon="check">Mentorship style: aligned</ReportLine>
        <ReportLine icon="warn">One concern: pace of publications</ReportLine>
      </div>
    </div>
  );
}

function ReportLine({ icon, children }: { icon: 'check' | 'warn'; children: React.ReactNode }) {
  if (icon === 'check') {
    return (
      <div className="flex items-start gap-2 text-ink">
        <svg width="14" height="14" viewBox="0 0 14 14" className="mt-0.5 text-forest shrink-0">
          <path
            d="M2 7.5l3 3 7-7"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span>{children}</span>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-2 text-soft">
      <svg width="14" height="14" viewBox="0 0 14 14" className="mt-0.5 text-gold shrink-0">
        <circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M7 4v3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="7" cy="9.7" r="0.7" fill="currentColor" />
      </svg>
      <span>{children}</span>
    </div>
  );
}

function SmallRadar() {
  const scores = [0.88, 0.82, 0.74, 0.9, 0.68];
  const cx = 60;
  const cy = 60;
  const R = 45;
  const angle = (i: number) => -Math.PI / 2 + (2 * Math.PI * i) / scores.length;

  const polyPoints = scores
    .map((s, i) => `${cx + Math.cos(angle(i)) * R * s},${cy + Math.sin(angle(i)) * R * s}`)
    .join(' ');

  const grid = [0.4, 0.7, 1.0].map((scale) =>
    scores
      .map((_, i) => `${cx + Math.cos(angle(i)) * R * scale},${cy + Math.sin(angle(i)) * R * scale}`)
      .join(' ')
  );

  return (
    <svg viewBox="0 0 120 120" className="w-full h-32">
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
        fillOpacity="0.20"
        stroke="var(--color-forest)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ───────────────────────── Feature stripe ───────────────────────── */

function Feature({
  eyebrow,
  headline,
  body,
  visual,
  align,
}: {
  eyebrow: string;
  headline: string;
  body: string;
  visual: React.ReactNode;
  align: 'left' | 'right';
}) {
  const visualFirst = align === 'left';
  return (
    <section className="border-t border-line/60 px-6 py-24 md:py-32">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 md:gap-20 items-center">
        <div className={visualFirst ? 'order-2 md:order-1' : 'order-2'}>
          <p className="font-sans text-xs uppercase tracking-[0.18em] text-forest mb-4">
            {eyebrow}
          </p>
          <h2 className="font-display font-light tracking-tight text-ink text-3xl md:text-5xl leading-[1.08]">
            {headline}
          </h2>
          <p className="mt-6 text-base md:text-lg text-muted leading-relaxed max-w-md">{body}</p>
        </div>
        <div className={visualFirst ? 'order-1 md:order-2' : 'order-1 md:order-1'}>
          <div className="flex justify-center">{visual}</div>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── Feature visuals ───────────────────────── */

function ResearchFitVisual() {
  return (
    <div className="w-full max-w-md">
      <div className="rounded-2xl bg-bone border border-line p-6 shadow-[0_24px_60px_-30px_rgba(21,23,26,0.25)]">
        <div className="flex items-center justify-between mb-5">
          <div className="font-display text-sm text-muted">Research overlap</div>
          <div className="font-display tabular text-2xl text-forest leading-none">92</div>
        </div>

        <div className="space-y-4">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-soft mb-1.5">Your background</div>
            <p className="text-sm text-ink leading-relaxed">
              Worked on <Hl>protein structure</Hl> prediction using{' '}
              <Hl>diffusion-based generative models</Hl> and developed MSA-free embeddings during
              undergrad research.
            </p>
          </div>

          <div className="flex items-center gap-2 text-soft">
            <span className="h-px flex-1 bg-line" />
            <svg width="14" height="14" viewBox="0 0 14 14">
              <path
                d="M2 7h10M8 3l4 4-4 4"
                stroke="currentColor"
                strokeWidth="1.5"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="h-px flex-1 bg-line" />
          </div>

          <div>
            <div className="text-[11px] uppercase tracking-wider text-soft mb-1.5">
              Dr. Liu, NeurIPS 2025
            </div>
            <p className="text-sm text-ink leading-relaxed italic">
              "We introduce a <Hl>diffusion-based generative model</Hl> for{' '}
              <Hl>protein structure</Hl> design that operates without multiple sequence alignments…"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Hl({ children }: { children: React.ReactNode }) {
  return (
    <span className="bg-forest-soft text-forest-dark px-1 rounded-sm">{children}</span>
  );
}

function ChatVisual() {
  return (
    <div className="w-full max-w-md space-y-3">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-sm font-medium shrink-0">
          KL
        </div>
        <div className="rounded-2xl rounded-tl-sm bg-bone border border-line px-4 py-3 shadow-[0_8px_24px_-12px_rgba(21,23,26,0.18)]">
          <p className="text-sm text-ink leading-relaxed">
            Tell me about your protein folding work — did you use AlphaFold's MSA pipeline, or roll
            your own embedding? I'm curious because my lab just published on the latter.
          </p>
        </div>
      </div>
      <div className="flex items-start gap-3 flex-row-reverse">
        <div className="w-9 h-9 rounded-full bg-ink/10 text-ink flex items-center justify-center text-xs font-medium shrink-0">
          You
        </div>
        <div className="rounded-2xl rounded-tr-sm bg-forest text-ivory px-4 py-3 shadow-[0_8px_24px_-12px_rgba(47,74,58,0.4)]">
          <p className="text-sm leading-relaxed">
            We trained an MSA-free model on a curated subset of CATH — happy to walk through how we
            handled the long-tail families.
          </p>
        </div>
      </div>
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-sm font-medium shrink-0">
          KL
        </div>
        <div className="rounded-2xl rounded-tl-sm bg-bone border border-line px-4 py-3 shadow-[0_8px_24px_-12px_rgba(21,23,26,0.18)]">
          <p className="text-sm text-ink leading-relaxed">
            That's exactly the regime we struggle with. One question — how did you handle
            evaluation when ground-truth structures are sparse?
          </p>
        </div>
      </div>
    </div>
  );
}

function ReportVisual() {
  return (
    <div className="w-full max-w-md rounded-2xl bg-bone border border-line p-7 shadow-[0_30px_70px_-25px_rgba(21,23,26,0.28)]">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="font-display text-sm text-muted tracking-tight">Chemistry Report</div>
          <div className="text-xs text-soft mt-0.5">Dr. Karen Liu · Caltech</div>
        </div>
        <div className="font-display tabular text-5xl text-ink leading-none">87</div>
      </div>

      <div className="mt-6 space-y-3">
        <DimRow label="Research alignment" value={92} />
        <DimRow label="Mentorship compatibility" value={84} />
        <DimRow label="Culture fit" value={78} />
        <DimRow label="Communication" value={88} />
        <DimRow label="No red flags" value={91} />
      </div>

      <div className="mt-6 pt-5 border-t border-line">
        <div className="text-[11px] uppercase tracking-wider text-soft mb-2">
          Intro email — draft
        </div>
        <p className="text-sm text-ink leading-relaxed italic">
          "Dear Dr. Liu, I came across your recent NeurIPS paper on MSA-free diffusion models for
          protein structure and was struck by…"
        </p>
        <button className="mt-3 text-xs font-medium text-forest hover:text-forest-dark transition-colors">
          Review full draft →
        </button>
      </div>
    </div>
  );
}

function DimRow({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <div className="text-xs text-muted">{label}</div>
        <div className="font-display tabular text-sm text-ink">{value}</div>
      </div>
      <div className="h-1 rounded-full bg-line/70 overflow-hidden">
        <div
          className="h-full bg-forest rounded-full"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

/* ───────────────────────── Final CTA ───────────────────────── */

function FinalCTA() {
  return (
    <section className="border-t border-line/60 px-6 py-28 md:py-36">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="font-display font-light tracking-tight text-ink text-4xl md:text-6xl leading-[1.05]">
          Ready to find your advisor?
        </h2>
        <p className="mt-6 text-lg text-muted">
          Five minutes of questions. The rest is on us.
        </p>
        <div className="mt-10">
          <Link
            to="/survey"
            className="inline-flex items-center gap-2 bg-forest text-ivory text-base font-medium px-8 py-3.5 rounded-full hover:bg-forest-dark transition-colors shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)]"
          >
            Start your match
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── Footer ───────────────────────── */

function Footer() {
  return (
    <footer className="border-t border-line/60 px-6 py-10">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-soft">
        <div className="font-display text-ink text-sm">PiMatch</div>
        <div className="flex items-center gap-5">
          <span>Hacktech 2026</span>
          <span aria-hidden>·</span>
          <span>Built with Claude</span>
        </div>
      </div>
    </footer>
  );
}
