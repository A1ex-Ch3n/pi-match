import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitSurvey, uploadCV } from '../api/client';
import type { StudentProfile } from '../types';

type FormData = Omit<StudentProfile, 'id'>;

const SLIDER_FIELDS: {
  key: keyof FormData;
  label: string;
  lowLabel: string;
  highLabel: string;
}[] = [
  {
    key: 'independence_preference',
    label: 'Independence Preference',
    lowLabel: 'Fully guided',
    highLabel: 'Fully autonomous',
  },
  {
    key: 'intervention_tolerance',
    label: 'Intervention Tolerance',
    lowLabel: 'High PI involvement',
    highLabel: 'Minimal PI involvement',
  },
  {
    key: 'meeting_frequency_preference',
    label: 'Meeting Frequency',
    lowLabel: 'Daily',
    highLabel: 'Monthly or less',
  },
  {
    key: 'work_life_balance_importance',
    label: 'Work-Life Balance',
    lowLabel: 'Not a priority',
    highLabel: 'Very important',
  },
  {
    key: 'industry_connections_importance',
    label: 'Industry Connections',
    lowLabel: 'Not important',
    highLabel: 'Very important',
  },
  {
    key: 'publication_rate_importance',
    label: 'Publication Rate',
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
    <div className="space-y-1">
      <div className="flex justify-between items-baseline">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-bold text-violet-600">{value}/5</span>
      </div>
      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-violet-600"
      />
      <div className="flex justify-between text-xs text-gray-400">
        <span>1 — {lowLabel}</span>
        <span>5 — {highLabel}</span>
      </div>
    </div>
  );
}

function parseList(val: string): string[] {
  return val
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
}

export default function SurveyPage() {
  const navigate = useNavigate();
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
  const [serverStatus, setServerStatus] = useState<'checking' | 'ready' | 'slow'>('checking');

  // Ping backend on mount: wakes Render from sleep + drives the status indicator
  useEffect(() => {
    const base = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace('/api', '');
    const start = Date.now();
    const slowTimer = setTimeout(() => setServerStatus('slow'), 3000);
    fetch(`${base}/health`)
      .then(() => {
        clearTimeout(slowTimer);
        setServerStatus('ready');
        console.log(`Backend ready in ${Date.now() - start}ms`);
      })
      .catch(() => {
        clearTimeout(slowTimer);
        setServerStatus('slow');
      });
    return () => clearTimeout(slowTimer);
  }, []);

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
        // Only retry on infrastructure errors (cold-start 404/503/502), not content errors
        const isInfraError = !status || status === 404 || status === 502 || status === 503;
        if (attempt === 0 && isInfraError) {
          setError('Server is warming up — retrying in 15 seconds…');
          await new Promise(r => setTimeout(r, 15000));
          setError('');
          continue;
        }
        const msg = status === 415
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

  function set<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload: FormData = {
        ...form,
        technical_skills: parseList(skillsInput),
        known_professors: parseList(professorsInput),
        preferred_research_topics: parseList(topicsInput),
      };
      // Step 1: create the student profile
      const student = await submitSurvey(payload);
      localStorage.setItem('lastStudentId', String(student.id));

      // Step 2: navigate immediately — match page runs matching on its own
      navigate(`/matches/${student.id}`);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      const status = (err as { response?: { status?: number } })?.response?.status;
      const msg = detail
        ?? (status ? `Error ${status} — please try again.` : 'Could not reach the server. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">
        {lastStudentId && (
          <div className="mb-4 flex items-center justify-between bg-violet-50 border border-violet-200 rounded-xl px-4 py-3">
            <span className="text-sm text-violet-700">You have a previous session.</span>
            <a
              href={`/matches/${lastStudentId}`}
              className="text-sm font-medium text-violet-700 hover:underline"
            >
              ← Back to your matches
            </a>
          </div>
        )}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-bold text-gray-900">PiMatch</h1>
            {serverStatus === 'checking' && (
              <span className="flex items-center gap-1.5 text-xs text-gray-400">
                <span className="w-2 h-2 rounded-full bg-gray-300 animate-pulse" />
                Connecting…
              </span>
            )}
            {serverStatus === 'ready' && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-600">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Server ready
              </span>
            )}
            {serverStatus === 'slow' && (
              <span className="flex items-center gap-1.5 text-xs text-amber-600">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                Server warming up — first request may take ~30s
              </span>
            )}
          </div>
          <p className="text-gray-500 mt-1">Find your ideal PhD advisor. Answer a few questions to get started.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Academic Background */}
          <section className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Academic Background</h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  required
                  type="text"
                  value={form.name}
                  onChange={e => set('name', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="Jane Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">GPA</label>
                <input
                  required
                  type="number"
                  step="0.01"
                  min={0}
                  max={4}
                  value={form.gpa}
                  onChange={e => set('gpa', parseFloat(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Years of Research Experience</label>
                <input
                  required
                  type="number"
                  min={0}
                  value={form.years_research_experience}
                  onChange={e => set('years_research_experience', parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Field of Study</label>
                <input
                  required
                  type="text"
                  value={form.field_of_study}
                  onChange={e => set('field_of_study', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="e.g. Computational Biology, Machine Learning"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Research Background</label>
                <textarea
                  required
                  rows={4}
                  value={form.research_background}
                  onChange={e => set('research_background', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="Describe your research experience, projects, and interests in detail. This is used for semantic matching against PI abstracts."
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Technical Skills <span className="text-gray-400 font-normal">(comma-separated)</span></label>
                <input
                  type="text"
                  value={skillsInput}
                  onChange={e => setSkillsInput(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="Python, PyTorch, wet lab, CRISPR, R"
                />
              </div>

              <div className="col-span-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.has_publications}
                    onChange={e => set('has_publications', e.target.checked)}
                    className="accent-violet-600 w-4 h-4"
                  />
                  <span className="text-sm font-medium text-gray-700">I have publications</span>
                </label>
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">CV / Resume <span className="text-gray-400 font-normal">(optional — upload file or paste text)</span></label>
                <div className="flex items-center gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => cvInputRef.current?.click()}
                    disabled={cvUploading}
                    className="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors border border-gray-300"
                  >
                    {cvUploading ? '⏳ Uploading...' : '📎 Upload CV'}
                  </button>
                  {cvFileName && !cvUploading && (
                    <span className="text-xs text-gray-500">✓ {cvFileName}</span>
                  )}
                  <input
                    ref={cvInputRef}
                    type="file"
                    accept=".txt,.pdf,.docx"
                    className="hidden"
                    onChange={handleCvUpload}
                  />
                </div>
                <textarea
                  rows={3}
                  value={form.cv_text ?? ''}
                  onChange={e => set('cv_text', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="Or paste your CV / personal statement here for richer matching..."
                />
              </div>
            </div>
          </section>

          {/* Connections & Research Topics */}
          <section className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Connections & Research Interests</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Professors You Know Personally <span className="text-gray-400 font-normal">(comma-separated)</span>
              </label>
              <input
                type="text"
                value={professorsInput}
                onChange={e => setProfessorsInput(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                placeholder="Prof. John Smith, Dr. Jane Doe"
              />
              <p className="text-xs text-gray-400 mt-1">Used to detect direct and indirect connections with PIs.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Research Topics <span className="text-gray-400 font-normal">(comma-separated)</span>
              </label>
              <input
                type="text"
                value={topicsInput}
                onChange={e => setTopicsInput(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                placeholder="protein folding, genomics, NLP, robotics"
              />
            </div>
          </section>

          {/* Preferences */}
          <section className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Preferences</h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Location Preference <span className="text-gray-400 font-normal">(select all that apply)</span></label>
                <div className="flex flex-wrap gap-2">
                  {(['any', 'west_coast', 'east_coast', 'midwest'] as const).map(loc => {
                    const labels: Record<string, string> = { any: 'No preference', west_coast: 'West Coast', east_coast: 'East Coast', midwest: 'Midwest' };
                    const prefs = form.location_preference as string[];
                    const checked = prefs.includes(loc);
                    return (
                      <label key={loc} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer text-sm transition-colors ${checked ? 'border-violet-500 bg-violet-50 text-violet-700 font-medium' : 'border-gray-300 text-gray-600 hover:border-gray-400'}`}>
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={checked}
                          onChange={e => {
                            const current = prefs.filter(p => p !== 'any');
                            if (loc === 'any') {
                              set('location_preference', ['any']);
                            } else if (e.target.checked) {
                              const next = current.filter(p => p !== loc).concat(loc);
                              set('location_preference', next.length ? next : ['any']);
                            } else {
                              const next = current.filter(p => p !== loc);
                              set('location_preference', next.length ? next : ['any']);
                            }
                          }}
                        />
                        {labels[loc]}
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Citizenship Status</label>
                <select
                  value={form.citizenship_status}
                  onChange={e => set('citizenship_status', e.target.value as FormData['citizenship_status'])}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="us_citizen">US Citizen</option>
                  <option value="pr">Permanent Resident</option>
                  <option value="f1">F-1 Visa</option>
                  <option value="j1">J-1 Visa</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Lab Size</label>
                <select
                  value={form.preferred_lab_size}
                  onChange={e => set('preferred_lab_size', e.target.value as FormData['preferred_lab_size'])}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="small">Small (1–5 students)</option>
                  <option value="medium">Medium (6–12 students)</option>
                  <option value="large">Large (13+ students)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Stipend ($/yr, optional)</label>
                <input
                  type="number"
                  min={0}
                  step={1000}
                  value={form.min_stipend ?? ''}
                  onChange={e => set('min_stipend', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="e.g. 38000"
                />
              </div>
            </div>
          </section>

          {/* Mentorship Style Sliders */}
          <section className="bg-white rounded-2xl border border-gray-200 p-6 space-y-5">
            <h2 className="text-lg font-semibold text-gray-900">Mentorship Style Preferences</h2>
            <p className="text-sm text-gray-500">Rate each dimension from 1–5. These are used to match you with a PI whose advising style fits yours.</p>

            {SLIDER_FIELDS.map(({ key, label, lowLabel, highLabel }) => (
              <SliderField
                key={key}
                label={label}
                lowLabel={lowLabel}
                highLabel={highLabel}
                value={form[key] as number}
                onChange={v => set(key, v as FormData[typeof key])}
              />
            ))}
          </section>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white font-semibold py-3 px-6 rounded-xl transition-colors text-base"
          >
            {loading ? 'Finding your matches...' : 'Find My PI Matches →'}
          </button>
        </form>
      </div>
    </div>
  );
}
