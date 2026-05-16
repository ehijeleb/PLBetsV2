import { Badge } from "./ui/Badge";
import type { GoalMarkets, Outcome } from "@/lib/types";

interface BettingInsightBoxProps {
  homeName: string;
  awayName: string;
  predictedOutcome: Outcome;
  pHome: number;
  pDraw: number;
  pAway: number;
  goalMarkets: GoalMarkets;
}

function pct(x: number) {
  return `${(x * 100).toFixed(1)}%`;
}

function ImpliedOdds({ p }: { p: number }) {
  // Fair (no-vig) decimal odds = 1/p.
  const odds = p > 0.01 ? (1 / p).toFixed(2) : "—";
  return <span className="font-mono text-ink-muted text-xs">@ {odds}</span>;
}

export function BettingInsightBox({
  homeName,
  awayName,
  predictedOutcome,
  pHome,
  pDraw,
  pAway,
  goalMarkets,
}: BettingInsightBoxProps) {
  const oneX2Label =
    predictedOutcome === "HOME" ? `${homeName} to win` : predictedOutcome === "DRAW" ? "Draw" : `${awayName} to win`;
  const oneX2P = predictedOutcome === "HOME" ? pHome : predictedOutcome === "DRAW" ? pDraw : pAway;

  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-3 gap-3">
        <Market label="1X2" badge="MODEL PICK">
          <div className="font-display tracking-wide text-xl">{oneX2Label}</div>
          <div className="text-ink-muted text-sm flex items-center gap-2">
            {pct(oneX2P)} <ImpliedOdds p={oneX2P} />
          </div>
        </Market>
        <Market label="Over / Under 2.5">
          <div className="font-display tracking-wide text-xl">
            {goalMarkets.p_over_25 >= 0.5 ? "Over 2.5" : "Under 2.5"}
          </div>
          <div className="text-ink-muted text-sm flex items-center gap-2">
            {pct(Math.max(goalMarkets.p_over_25, goalMarkets.p_under_25))}{" "}
            <ImpliedOdds p={Math.max(goalMarkets.p_over_25, goalMarkets.p_under_25)} />
          </div>
        </Market>
        <Market label="Both teams to score">
          <div className="font-display tracking-wide text-xl">
            {goalMarkets.p_btts >= 0.5 ? "Yes (BTTS)" : "No (BTTS)"}
          </div>
          <div className="text-ink-muted text-sm flex items-center gap-2">
            {pct(goalMarkets.p_btts >= 0.5 ? goalMarkets.p_btts : 1 - goalMarkets.p_btts)}{" "}
            <ImpliedOdds p={goalMarkets.p_btts >= 0.5 ? goalMarkets.p_btts : 1 - goalMarkets.p_btts} />
          </div>
        </Market>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        <div className="bg-bg-tertiary rounded-lg p-3">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            Expected goals (Poisson)
          </div>
          <div className="flex items-baseline gap-3">
            <div>
              <div className="font-mono text-xl">{goalMarkets.expected_home_goals.toFixed(2)}</div>
              <div className="text-xs text-ink-muted">{homeName}</div>
            </div>
            <span className="text-ink-muted">—</span>
            <div>
              <div className="font-mono text-xl">{goalMarkets.expected_away_goals.toFixed(2)}</div>
              <div className="text-xs text-ink-muted">{awayName}</div>
            </div>
          </div>
        </div>
        <div className="bg-bg-tertiary rounded-lg p-3">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            Most likely scorelines
          </div>
          <div className="grid grid-cols-5 gap-2">
            {goalMarkets.p_correct_score_top.slice(0, 5).map((s, i) => (
              <div key={i} className="text-center">
                <div className="font-mono">{s.score}</div>
                <div className="text-[10px] text-ink-muted">{pct(s.prob)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <ResponsibleGamblingNote />
    </div>
  );
}

function Market({
  label,
  badge,
  children,
}: {
  label: string;
  badge?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-tertiary rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-widest text-ink-muted">{label}</span>
        {badge ? <Badge tone="green">{badge}</Badge> : null}
      </div>
      <div>{children}</div>
    </div>
  );
}

export function ResponsibleGamblingNote() {
  return (
    <p className="text-[11px] leading-relaxed text-ink-muted border-l-2 border-accent-amber/40 pl-3">
      <span className="text-accent-amber">⚠</span> For informational and entertainment purposes only.
      Gambling can be addictive. Please bet responsibly.
      <br />
      <a className="underline hover:text-ink" href="https://www.gamstop.co.uk" target="_blank" rel="noreferrer">
        GamStop
      </a>{" "}
      ·{" "}
      <a
        className="underline hover:text-ink"
        href="https://www.begambleaware.org"
        target="_blank"
        rel="noreferrer"
      >
        BeGambleAware
      </a>
    </p>
  );
}
