// Shared TypeScript types — mirrored from backend Pydantic schemas.

export type Outcome = "HOME" | "DRAW" | "AWAY";
export type ResultLetter = "W" | "D" | "L";
export type ConfidenceBand = "LOW" | "MEDIUM" | "HIGH";

export interface Team {
  id: number;
  name: string;
  short_name?: string | null;
  tla?: string | null;
  crest?: string | null;
}

export interface Fixture {
  id: number;
  matchday?: number | null;
  status: string;
  utc_date: string;
  home_team: Team;
  away_team: Team;
  competition: string;
  venue?: string | null;
  home_goals?: number | null;
  away_goals?: number | null;
}

export interface StandingRow {
  position: number;
  team: Team;
  played: number;
  won: number;
  draw: number;
  lost: number;
  points: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  form?: string | null;
}

export interface ShapFeature {
  feature: string;
  label: string;
  shap_value: number;
  contribution: "home" | "draw" | "away";
}

export interface GoalMarkets {
  expected_home_goals: number;
  expected_away_goals: number;
  p_btts: number;
  p_over_25: number;
  p_under_25: number;
  p_correct_score_top: { score: string; prob: number }[];
}

export interface FormMatch {
  date: string;
  opponent: string;
  venue: "H" | "A";
  goals_for: number;
  goals_against: number;
  result: ResultLetter;
}

export interface TeamForm {
  team: string;
  matches: FormMatch[];
  wins: number;
  draws: number;
  losses: number;
  goals_scored: number;
  goals_conceded: number;
  clean_sheets: number;
}

export interface H2HMatch {
  date: string;
  home_team: string;
  away_team: string;
  home_goals: number;
  away_goals: number;
}

export interface H2H {
  home_team: string;
  away_team: string;
  matches: H2HMatch[];
  home_wins: number;
  draws: number;
  away_wins: number;
}

export interface PredictResponse {
  id?: number;
  home_team: string;
  away_team: string;
  p_home: number;
  p_draw: number;
  p_away: number;
  predicted_outcome: Outcome;
  confidence: number;
  confidence_band: ConfidenceBand;
  shap_top: ShapFeature[];
  goal_markets: GoalMarkets;
  home_form?: TeamForm | null;
  away_form?: TeamForm | null;
  h2h?: H2H | null;
}

export interface HistoryRow {
  id: number;
  created_at: string;
  home_team: string;
  away_team: string;
  predicted_outcome: Outcome;
  p_home: number;
  p_draw: number;
  p_away: number;
  confidence: number;
  actual_outcome?: Outcome | null;
  actual_home_goals?: number | null;
  actual_away_goals?: number | null;
  correct?: boolean | null;
}

export interface HistoryResponse {
  rows: HistoryRow[];
  total: number;
  correct: number;
  accuracy: number | null;
}

export interface FormHeatmapTeam {
  team: string;
  results: ResultLetter[];
}

export interface HomeVsAwayTeam {
  team: string;
  home_win_rate: number;
  away_win_rate: number;
  home_played: number;
  away_played: number;
}
