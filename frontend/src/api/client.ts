import axios from 'axios';
import type { StudentProfile, PIProfile, MatchResult, ChemistryReport } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
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

export const simulate = (matchId: number, message: string): Promise<MatchResult> =>
  api.post<MatchResult>(`/simulate/${matchId}`, { message }).then(r => r.data);

export const evaluate = (matchId: number): Promise<ChemistryReport> =>
  api.post<ChemistryReport>(`/evaluate/${matchId}`).then(r => r.data);

export const getReport = (matchId: number): Promise<{ match: MatchResult; report: ChemistryReport }> =>
  api.get<{ match: MatchResult; report: ChemistryReport }>(`/report/${matchId}`).then(r => r.data);
