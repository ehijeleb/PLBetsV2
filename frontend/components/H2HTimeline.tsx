import clsx from "clsx";
import type { H2H } from "@/lib/types";

interface H2HTimelineProps {
  h2h: H2H;
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "2-digit" });
}

export function H2HTimeline({ h2h }: H2HTimelineProps) {
  if (!h2h?.matches?.length) {
    return <p className="text-ink-muted text-sm">No head-to-head data available.</p>;
  }
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div className="text-xs uppercase tracking-widest text-ink-muted">Last {h2h.matches.length} meetings</div>
        <div className="text-xs font-mono">
          <span className="text-accent-green">{h2h.home_wins}W</span>
          <span className="text-ink-muted"> · </span>
          <span className="text-accent-amber">{h2h.draws}D</span>
          <span className="text-ink-muted"> · </span>
          <span className="text-accent-red">{h2h.away_wins}L</span>
        </div>
      </div>
      <div className="space-y-2">
        {h2h.matches.map((m, i) => {
          const winner =
            m.home_goals > m.away_goals
              ? "home"
              : m.home_goals < m.away_goals
                ? "away"
                : "draw";
          return (
            <div
              key={i}
              className="grid grid-cols-[60px_1fr_auto_1fr_80px] items-center gap-2 text-sm"
            >
              <span className="text-ink-muted font-mono text-xs">{fmtDate(m.date)}</span>
              <span className="text-right truncate">{m.home_team}</span>
              <span
                className={clsx(
                  "px-2 py-0.5 font-mono text-xs rounded-md border",
                  winner === "home" && "border-accent-green/40 text-accent-green",
                  winner === "draw" && "border-accent-amber/40 text-accent-amber",
                  winner === "away" && "border-accent-red/40 text-accent-red",
                )}
              >
                {m.home_goals}–{m.away_goals}
              </span>
              <span className="truncate">{m.away_team}</span>
              <span className="text-ink-muted text-[10px] uppercase tracking-widest text-right">
                {winner === "home" ? "Home" : winner === "draw" ? "Draw" : "Away"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
