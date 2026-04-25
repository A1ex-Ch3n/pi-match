import axios from 'axios';
import type { StudentProfile, PIProfile, MatchResult, ChemistryReport, TranscriptMessage } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

export const submitSurvey = (data: Omit<StudentProfile, 'id'>): Promise<StudentProfile> =>
  api.post<StudentProfile>('/survey', data).then(r => r.data);

export const listPIs = (): Promise<PIProfile[]> =>
  api.get<PIProfile[]>('/pi/list').then(r => r.data);

export const seedPIs = (): Promise<unknown> =>
  api.post('/pi/seed').then(r => r.data);

export const runMatch = (studentId: number): Promise<MatchResult[]> =>
  api.post<MatchResult[]>(`/match/${studentId}`).then(r => r.data);

export const getMatches = (studentId: number): Promise<MatchResult[]> =>
  api.get<MatchResult[]>(`/matches/${studentId}`).then(r => r.data);

export const getMatch = (matchId: number): Promise<MatchResult> =>
  api.get<MatchResult>(`/match/${matchId}`).then(r => r.data);

export interface SimulateResponse {
  pi_response: string;
  transcript: TranscriptMessage[];
  match_id: number;
}

export const simulate = (matchId: number, message: string): Promise<SimulateResponse> =>
  api.post<SimulateResponse>(`/simulate/${matchId}`, { message }).then(r => r.data);

export const evaluate = (matchId: number): Promise<ChemistryReport> =>
  api.post<ChemistryReport>(`/evaluate/${matchId}`).then(r => r.data);

export const getReport = (matchId: number): Promise<{ match: MatchResult; report: ChemistryReport }> =>
  api.get<{ match: MatchResult; report: ChemistryReport }>(`/report/${matchId}`).then(r => r.data);

export const uploadCV = (file: File): Promise<{ cv_text: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ cv_text: string }>('/upload-cv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};
