// Thin API client + SWR fetcher. Reads NEXT_PUBLIC_API_URL at build time.

import type {
  Fixture,
  HistoryResponse,
  PredictResponse,
  StandingRow,
  TeamForm,
  H2H,
  FormHeatmapTeam,
  HomeVsAwayTeam,
} from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body.slice(0, 200)}`);
  }
}

export async function fetcher<T>(path: string): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json() as Promise<T>;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json() as Promise<T>;
}

// ── Typed helpers ──────────────────────────────────────────────────────────

export const api = {
  upcomingFixtures: (limit = 10) =>
    fetcher<{ fixtures: Fixture[]; source: string }>(`/api/fixtures/upcoming?limit=${limit}`),
  standings: () =>
    fetcher<{ season: string | null; rows: StandingRow[] }>(`/api/standings`),
  teams: () => fetcher<{ teams: string[] }>(`/api/stats/teams`),
  referees: (min = 10) =>
    fetcher<{ referees: string[] }>(`/api/stats/referees?min_matches=${min}`),
  teamForm: (team: string, last = 10) =>
    fetcher<TeamForm>(`/api/stats/form/${encodeURIComponent(team)}?last=${last}`),
  h2h: (home: string, away: string, last = 10) =>
    fetcher<H2H>(`/api/stats/h2h/${encodeURIComponent(home)}/${encodeURIComponent(away)}?last=${last}`),
  formHeatmap: (last = 10) =>
    fetcher<{ teams: FormHeatmapTeam[] }>(`/api/stats/form-heatmap?last=${last}`),
  homeVsAway: () =>
    fetcher<{ teams: HomeVsAwayTeam[] }>(`/api/stats/home-vs-away`),
  history: (sessionId?: string, limit = 100) =>
    fetcher<HistoryResponse>(
      `/api/predict/history?limit=${limit}${sessionId ? `&session_id=${encodeURIComponent(sessionId)}` : ""}`,
    ),
  predict: (body: {
    home_team: string;
    away_team: string;
    referee?: string | null;
    kickoff?: string | null;
    session_id?: string | null;
    fixture_id?: number | null;
  }) => postJson<PredictResponse>(`/api/predict`, body),
};

// Stable per-browser session id (anchors prediction history).
export function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  const k = "plbets-session";
  let s = window.localStorage.getItem(k);
  if (!s) {
    s = `s_${Math.random().toString(36).slice(2)}_${Date.now().toString(36)}`;
    window.localStorage.setItem(k, s);
  }
  return s;
}
