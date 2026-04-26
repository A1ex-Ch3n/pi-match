import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { submitSurvey, uploadCV } from '../api/client';
import type { StudentProfile } from '../types';

type FormData = Omit<StudentProfile, 'id'>;

const TOTAL_STEPS = 4;

const SLIDER_FIELDS: {
  key: keyof FormData;
  label: string;
  lowLabel: string;
  highLabel: string;
}[] = [
  {
    key: 'independence_preference',
    label: 'Independence',
    lowLabel: 'Fully guided',
    highLabel: 'Fully autonomous',
  },
  {
    key: 'intervention_tolerance',
    label: 'PI involvement',
    lowLabel: 'Hands-on',
    highLabel: 'Hands-off',
  },
  {
    key: 'meeting_frequency_preference',
    label: 'Meeting cadence',
    lowLabel: 'Daily',
    highLabel: 'Monthly+',
  },
  {
    key: 'work_life_balance_importance',
    label: 'Work–life balance',
    lowLabel: 'Not a priority',
    highLabel: 'Very important',
  },
  {
    key: 'industry_connections_importance',
    label: 'Industry connections',
    lowLabel: 'Not important',
    highLabel: 'Very important',
  },
  {
    key: 'publication_rate_importance',
    label: 'Publication rate',
    lowLabel: 'Not a priority',
    highLabel: 'Top priority',
  },
];

const DEFAULT: FormData = {
  name: '',
  gpa: 3.5,
  field_of_study: '',
  research_background: '',
  technical_skills: [],
  years_research_experience: 1,
  has_publications: false,
  cv_text: '',
  known_professors: [],
  preferred_research_topics: [],
  location_preference: ['any'],
  citizenship_status: 'f1',
  min_stipend: undefined,
  preferred_lab_size: 'medium',
  independence_preference: 3,
  intervention_tolerance: 3,
  meeting_frequency_preference: 3,
  work_life_balance_importance: 3,
  industry_connections_importance: 3,
  publication_rate_importance: 3,
};

function parseList(val: string): string[] {
  return val
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

/* ───────────────────────── Page ───────────────────────── */

export default function SurveyPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormData>(DEFAULT);
  const [skillsInput, setSkillsInput] = useState('');
  const [professorsInput, setProfessorsInput] = useState('');
  const [topicsInput, setTopicsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cvUploading, setCvUploading] = useState(false);
  const [cvFileName, setCvFileName] = useState('');
  const cvInputRef = useRef<HTMLInputElement>(null);
  const lastStudentId = localStorage.getItem('lastStudentId');
  const [serverStatus, setServerStatus] = useState<'checking' | 'ready' | 'no_key' | 'slow'>(
    'checking'
  );

  useEffect(() => {
    const base = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace('/api', '');
    const start = Date.now();
    const slowTimer = setTimeout(() => setServerStatus('slow'), 3000);
    fetch(`${base}/health`)
      .then((r) => r.json())
      .then((data: { status: string; api_key_configured?: boolean }) => {
        clearTimeout(slowTimer);
        setServerStatus(data.api_key_configured === false ? 'no_key' : 'ready');
        console.log(`Backend ready in ${Date.now() - start}ms`);
      })
      .catch(() => {
        clearTimeout(slowTimer);
        setServerStatus('slow');
      });
    return () => clearTimeout(slowTimer);
  }, []);

  function set<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleCvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setCvUploading(true);
    setCvFileName(file.name);
    setError('');
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const result = await uploadCV(file);
        set('cv_text', result.cv_text);
        setCvUploading(false);
        return;
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        const isInfraError = !status || status === 404 || status === 502 || status === 503;
        if (attempt === 0 && isInfraError) {
          setError('Server is warming up — retrying in 15 seconds…');
          await new Promise((r) => setTimeout(r, 15000));
          setError('');
          continue;
        }
        const msg =
          status === 415
            ? 'Unsupported file type. Please upload a .txt or .pdf file.'
            : status === 501
            ? 'PDF parsing unavailable on the server. Please paste your CV text below.'
            : isInfraError
            ? 'Server is still starting — please wait 30 seconds and try again.'
            : (err as Error).message ?? 'Upload failed. Please paste your CV text below.';
        setError(msg);
        break;
      }
    }
    setCvUploading(false);
  }

  async function handleSubmit() {
    setError('');
    setLoading(true);
    try {
      const payload: FormData = {
        ...form,
        technical_skills: parseList(skillsInput),
        known_professors: parseList(professorsInput),
        preferred_research_topics: parseList(topicsInput),
      };
      const student = await submitSurvey(payload);
      localStorage.setItem('lastStudentId', String(student.id));
      navigate(`/matches/${student.id}`);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const status = (err as { response?: { status?: number } })?.response?.status;
      const msg =
        detail ??
        (status ? `Error ${status} — please try again.` : 'Could not reach the server. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  const stepValid = useMemo(() => {
    if (step === 1) {
      return (
        form.name.trim().length > 0 &&
        form.field_of_study.trim().length > 0 &&
        form.gpa > 0 &&
        form.gpa <= 4 &&
        form.years_research_experience >= 0
      );
    }
    if (step === 2) {
      return form.research_background.trim().length > 0;
    }
    return true;
  }, [step, form]);

  function goNext() {
    if (!stepValid) return;
    if (step < TOTAL_STEPS) {
      setStep((s) => s + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      handleSubmit();
    }
  }

  function goBack() {
    setStep((s) => Math.max(1, s - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const stepTitles = ['About you', 'Your research', 'Your situation', 'Mentorship style'];

  return (
    <div className="min-h-screen bg-ivory text-ink flex flex-col">
      <Nav serverStatus={serverStatus} />
      <ProgressBar step={step} total={TOTAL_STEPS} />

      <main className="flex-1 px-6 pt-12 md:pt-16 pb-24">
        <div className="max-w-2xl mx-auto">
          {step === 1 && lastStudentId && (
            <div className="mb-8 flex items-center justify-between bg-forest-soft border border-forest/15 rounded-xl px-4 py-3">
              <span className="text-sm text-forest-dark">You have a previous session.</span>
              <Link
                to={`/matches/${lastStudentId}`}
                className="text-sm font-medium text-forest hover:text-forest-dark"
              >
                Back to your matches →
              </Link>
            </div>
          )}

          <div className="mb-10">
            <p className="font-sans text-xs uppercase tracking-[0.18em] text-soft mb-3">
              Step {step} of {TOTAL_STEPS}
            </p>
            <h1 className="font-display font-light tracking-tight text-ink text-4xl md:text-5xl leading-[1.05]">
              {stepTitles[step - 1]}
            </h1>
          </div>

          <div key={step} className="step-enter">
            {step === 1 && <Step1 form={form} set={set} />}
            {step === 2 && (
              <Step2
                form={form}
                set={set}
                skillsInput={skillsInput}
                setSkillsInput={setSkillsInput}
                topicsInput={topicsInput}
                setTopicsInput={setTopicsInput}
                cvFileName={cvFileName}
                cvUploading={cvUploading}
                onUploadClick={() => cvInputRef.current?.click()}
                cvInputRef={cvInputRef}
                onCvUpload={handleCvUpload}
              />
            )}
            {step === 3 && (
              <Step3
                form={form}
                set={set}
                professorsInput={professorsInput}
                setProfessorsInput={setProfessorsInput}
              />
            )}
            {step === 4 && <Step4 form={form} set={set} />}
          </div>

          {error && (
            <div className="mt-6 bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <Footer
            step={step}
            total={TOTAL_STEPS}
            valid={stepValid}
            loading={loading}
            onBack={goBack}
            onNext={goNext}
          />
        </div>
      </main>
    </div>
  );
}

/* ───────────────────────── Nav ───────────────────────── */

function Nav({ serverStatus }: { serverStatus: 'checking' | 'ready' | 'no_key' | 'slow' }) {
  return (
    <nav className="sticky top-0 z-50 bg-ivory/85 backdrop-blur border-b border-line/70">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="font-display text-lg font-medium tracking-tight text-ink">
          PiMatch
        </Link>
        <div className="flex items-center gap-5">
          <ServerStatusPill status={serverStatus} />
          <Link
            to="/"
            className="text-sm font-medium text-soft hover:text-ink transition-colors"
          >
            ← Home
          </Link>
        </div>
      </div>
    </nav>
  );
}

function ServerStatusPill({ status }: { status: 'checking' | 'ready' | 'no_key' | 'slow' }) {
  const config = {
    checking: { dot: 'bg-soft animate-pulse', label: 'Connecting' },
    ready: { dot: 'bg-forest', label: 'Server ready' },
    no_key: { dot: 'bg-gold', label: 'API key missing' },
    slow: { dot: 'bg-gold animate-pulse', label: 'Server warming up' },
  }[status];
  return (
    <span className="hidden sm:flex items-center gap-1.5 text-xs text-soft">
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}

/* ───────────────────────── Progress bar ───────────────────────── */

function ProgressBar({ step, total }: { step: number; total: number }) {
  const pct = (step / total) * 100;
  return (
    <div className="h-0.5 bg-line/40">
      <div
        className="h-full bg-forest transition-[width] duration-500 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/* ───────────────────────── Footer (back / continue) ───────────────────────── */

function Footer({
  step,
  total,
  valid,
  loading,
  onBack,
  onNext,
}: {
  step: number;
  total: number;
  valid: boolean;
  loading: boolean;
  onBack: () => void;
  onNext: () => void;
}) {
  const isLast = step === total;
  return (
    <div className="mt-12 flex items-center justify-between">
      {step > 1 ? (
        <button
          type="button"
          onClick={onBack}
          disabled={loading}
          className="text-sm font-medium text-soft hover:text-ink transition-colors disabled:opacity-50"
        >
          ← Back
        </button>
      ) : (
        <span />
      )}

      <button
        type="button"
        onClick={onNext}
        disabled={!valid || loading}
        className="inline-flex items-center gap-2 bg-forest text-ivory text-sm font-medium px-7 py-3 rounded-full hover:bg-forest-dark transition-colors disabled:bg-soft/40 disabled:text-ivory/70 disabled:cursor-not-allowed shadow-[0_8px_24px_-8px_rgba(47,74,58,0.45)] disabled:shadow-none"
      >
        {loading ? (
          <>
            <Spinner /> Finding your matches…
          </>
        ) : isLast ? (
          <>
            Find my matches <span aria-hidden>→</span>
          </>
        ) : (
          <>
            Continue <span aria-hidden>→</span>
          </>
        )}
      </button>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path
        d="M22 12a10 10 0 0 0-10-10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* ───────────────────────── Field primitives ───────────────────────── */

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-[0.14em] text-soft mb-2">{label}</label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-soft">{hint}</p>}
    </div>
  );
}

const inputCls =
  'w-full bg-bone border border-line rounded-xl px-4 py-3 text-base text-ink placeholder:text-soft/70 focus:outline-none focus:border-forest focus:ring-4 focus:ring-forest/10 transition-all';

const textareaCls = inputCls + ' resize-none leading-relaxed';

function ChipPreview({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-2.5 flex flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          key={item}
          className="text-xs px-2.5 py-1 rounded-full bg-forest-soft text-forest-dark font-medium"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function PillToggle<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string }[];
}) {
  return (
    <div className="inline-flex p-1 bg-bone border border-line rounded-full">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`px-4 py-1.5 text-sm rounded-full transition-all ${
              active
                ? 'bg-forest text-ivory font-medium shadow-[0_2px_6px_-2px_rgba(47,74,58,0.5)]'
                : 'text-muted hover:text-ink'
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

/* ───────────────────────── Step 1 — About you ───────────────────────── */

function Step1({
  form,
  set,
}: {
  form: FormData;
  set: <K extends keyof FormData>(k: K, v: FormData[K]) => void;
}) {
  return (
    <div className="space-y-7">
      <Field label="Full name">
        <input
          type="text"
          value={form.name}
          onChange={(e) => set('name', e.target.value)}
          className={inputCls}
          placeholder="Jane Doe"
          autoFocus
        />
      </Field>

      <Field label="Field of study">
        <input
          type="text"
          value={form.field_of_study}
          onChange={(e) => set('field_of_study', e.target.value)}
          className={inputCls}
          placeholder="Computational Biology, Machine Learning, …"
        />
      </Field>

      <div className="grid grid-cols-2 gap-5">
        <Field label="GPA" hint="On a 4.0 scale">
          <input
            type="number"
            step="0.01"
            min={0}
            max={4}
            value={form.gpa}
            onChange={(e) => set('gpa', parseFloat(e.target.value))}
            className={inputCls + ' tabular'}
          />
        </Field>
        <Field label="Years of research experience">
          <input
            type="number"
            min={0}
            value={form.years_research_experience}
            onChange={(e) => set('years_research_experience', parseInt(e.target.value) || 0)}
            className={inputCls + ' tabular'}
          />
        </Field>
      </div>

      <Field label="Publications">
        <PillToggle
          value={form.has_publications ? 'yes' : 'no'}
          onChange={(v) => set('has_publications', v === 'yes')}
          options={[
            { value: 'no', label: 'Not yet' },
            { value: 'yes', label: 'Yes, I have publications' },
          ]}
        />
      </Field>
    </div>
  );
}

/* ───────────────────────── Step 2 — Your research ───────────────────────── */

function Step2({
  form,
  set,
  skillsInput,
  setSkillsInput,
  topicsInput,
  setTopicsInput,
  cvFileName,
  cvUploading,
  onUploadClick,
  cvInputRef,
  onCvUpload,
}: {
  form: FormData;
  set: <K extends keyof FormData>(k: K, v: FormData[K]) => void;
  skillsInput: string;
  setSkillsInput: (v: string) => void;
  topicsInput: string;
  setTopicsInput: (v: string) => void;
  cvFileName: string;
  cvUploading: boolean;
  onUploadClick: () => void;
  cvInputRef: React.RefObject<HTMLInputElement | null>;
  onCvUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-7">
      <Field
        label="Research background"
        hint="The more specific, the better — this is what we match against PIs' actual papers."
      >
        <textarea
          rows={6}
          value={form.research_background}
          onChange={(e) => set('research_background', e.target.value)}
          className={textareaCls}
          placeholder="Describe your projects, methods you've used, what excites you. e.g. 'I built MSA-free embeddings for protein structure prediction using diffusion models...'"
          autoFocus
        />
      </Field>

      <Field label="Technical skills" hint="Comma-separated">
        <input
          type="text"
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
          className={inputCls}
          placeholder="Python, PyTorch, wet lab, CRISPR, R"
        />
        <ChipPreview items={parseList(skillsInput)} />
      </Field>

      <Field label="Preferred research topics" hint="Comma-separated">
        <input
          type="text"
          value={topicsInput}
          onChange={(e) => setTopicsInput(e.target.value)}
          className={inputCls}
          placeholder="protein folding, genomics, NLP, robotics"
        />
        <ChipPreview items={parseList(topicsInput)} />
      </Field>

      <Field label="CV / Resume" hint="Optional — adds depth to the matching">
        <div className="flex items-center gap-3 mb-2.5">
          <button
            type="button"
            onClick={onUploadClick}
            disabled={cvUploading}
            className="inline-flex items-center gap-2 bg-bone hover:bg-line/40 disabled:opacity-50 text-ink text-sm font-medium px-4 py-2 rounded-full transition-colors border border-line"
          >
            {cvUploading ? (
              <>
                <Spinner /> Uploading…
              </>
            ) : (
              <>
                <UploadIcon /> Upload file
              </>
            )}
          </button>
          {cvFileName && !cvUploading && (
            <span className="text-xs text-soft inline-flex items-center gap-1.5">
              <CheckIcon /> {cvFileName}
            </span>
          )}
          <input
            ref={cvInputRef}
            type="file"
            accept=".txt,.pdf,.docx"
            className="hidden"
            onChange={onCvUpload}
          />
        </div>
        <textarea
          rows={4}
          value={form.cv_text ?? ''}
          onChange={(e) => set('cv_text', e.target.value)}
          className={textareaCls}
          placeholder="…or paste CV / personal statement text here."
        />
      </Field>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path
        d="M7 9V2M7 2L4 5M7 2l3 3M2 11h10"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 14 14" className="text-forest">
      <path
        d="M2 7.5l3 3 7-7"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ───────────────────────── Step 3 — Your situation ───────────────────────── */

function Step3({
  form,
  set,
  professorsInput,
  setProfessorsInput,
}: {
  form: FormData;
  set: <K extends keyof FormData>(k: K, v: FormData[K]) => void;
  professorsInput: string;
  setProfessorsInput: (v: string) => void;
}) {
  const locations = [
    { value: 'any', label: 'No preference' },
    { value: 'west_coast', label: 'West Coast' },
    { value: 'east_coast', label: 'East Coast' },
    { value: 'midwest', label: 'Midwest' },
  ] as const;

  const prefs = form.location_preference as string[];

  return (
    <div className="space-y-7">
      <Field
        label="Professors you know personally"
        hint="Used to detect direct and indirect (co-author) connections. Comma-separated."
      >
        <input
          type="text"
          value={professorsInput}
          onChange={(e) => setProfessorsInput(e.target.value)}
          className={inputCls}
          placeholder="Prof. John Smith, Dr. Jane Doe"
          autoFocus
        />
        <ChipPreview items={parseList(professorsInput)} />
      </Field>

      <Field label="Location preference" hint="Select all that apply">
        <div className="flex flex-wrap gap-2">
          {locations.map((loc) => {
            const checked = prefs.includes(loc.value);
            return (
              <button
                key={loc.value}
                type="button"
                onClick={() => {
                  const current = prefs.filter((p) => p !== 'any');
                  if (loc.value === 'any') {
                    set('location_preference', ['any']);
                  } else if (!checked) {
                    const next = current.filter((p) => p !== loc.value).concat(loc.value);
                    set('location_preference', next.length ? next : ['any']);
                  } else {
                    const next = current.filter((p) => p !== loc.value);
                    set('location_preference', next.length ? next : ['any']);
                  }
                }}
                className={`px-4 py-2 rounded-full text-sm transition-all border ${
                  checked
                    ? 'bg-forest text-ivory border-forest font-medium shadow-[0_2px_6px_-2px_rgba(47,74,58,0.45)]'
                    : 'bg-bone text-muted border-line hover:border-forest/40 hover:text-ink'
                }`}
              >
                {loc.label}
              </button>
            );
          })}
        </div>
      </Field>

      <div className="grid md:grid-cols-2 gap-5">
        <Field label="Citizenship status">
          <select
            value={form.citizenship_status}
            onChange={(e) =>
              set('citizenship_status', e.target.value as FormData['citizenship_status'])
            }
            className={inputCls + ' appearance-none bg-no-repeat bg-[right_1rem_center] pr-10'}
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%238B8B86' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\")",
            }}
          >
            <option value="us_citizen">US Citizen</option>
            <option value="pr">Permanent Resident</option>
            <option value="f1">F-1 Visa</option>
            <option value="j1">J-1 Visa</option>
            <option value="other">Other</option>
          </select>
        </Field>

        <Field label="Minimum stipend" hint="Optional, $/year">
          <input
            type="number"
            min={0}
            step={1000}
            value={form.min_stipend ?? ''}
            onChange={(e) =>
              set('min_stipend', e.target.value ? parseInt(e.target.value) : undefined)
            }
            className={inputCls + ' tabular'}
            placeholder="38000"
          />
        </Field>
      </div>

      <Field label="Preferred lab size">
        <PillToggle
          value={form.preferred_lab_size}
          onChange={(v) => set('preferred_lab_size', v)}
          options={[
            { value: 'small', label: 'Small · 1–5' },
            { value: 'medium', label: 'Medium · 6–12' },
            { value: 'large', label: 'Large · 13+' },
          ]}
        />
      </Field>
    </div>
  );
}

/* ───────────────────────── Step 4 — Mentorship style ───────────────────────── */

function Step4({
  form,
  set,
}: {
  form: FormData;
  set: <K extends keyof FormData>(k: K, v: FormData[K]) => void;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-muted leading-relaxed mb-8 -mt-4">
        Rate each dimension from 1 to 5. We use these to match you with a PI whose advising
        style fits yours.
      </p>
      <div className="space-y-8">
        {SLIDER_FIELDS.map(({ key, label, lowLabel, highLabel }) => (
          <SliderField
            key={key}
            label={label}
            lowLabel={lowLabel}
            highLabel={highLabel}
            value={form[key] as number}
            onChange={(v) => set(key, v as FormData[typeof key])}
          />
        ))}
      </div>
    </div>
  );
}

function SliderField({
  label,
  lowLabel,
  highLabel,
  value,
  onChange,
}: {
  label: string;
  lowLabel: string;
  highLabel: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2.5">
        <label className="text-sm font-medium text-ink">{label}</label>
        <span className="font-display tabular text-2xl text-forest leading-none">{value}</span>
      </div>
      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="range-forest"
      />
      <div className="flex justify-between text-xs text-soft mt-2">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );
}
