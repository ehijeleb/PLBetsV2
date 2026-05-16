"use client";
import { motion } from "framer-motion";
import { Button } from "./ui/Button";
import type { Fixture } from "@/lib/types";

interface MatchCardProps {
  fixture: Fixture;
  onAnalyse?: (home: string, away: string, fixtureId: number) => void;
  preProb?: { p_home: number; p_draw: number; p_away: number };
}

function fmtKickoff(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MatchCard({ fixture, onAnalyse, preProb }: MatchCardProps) {
  const { home_team, away_team } = fixture;
  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="min-w-[320px] bg-bg-secondary border border-line rounded-2xl p-4 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
        <span>{fmtKickoff(fixture.utc_date)}</span>
        <span>{fixture.competition}</span>
      </div>

      <div className="flex items-center justify-between gap-4">
        <TeamSide team={home_team} side="home" />
        <span className="font-display text-2xl text-ink-muted">vs</span>
        <TeamSide team={away_team} side="away" />
      </div>

      {preProb ? (
        <div className="flex h-1.5 rounded-full overflow-hidden bg-bg-tertiary">
          <div className="bg-accent-green" style={{ width: `${preProb.p_home * 100}%` }} />
          <div className="bg-accent-amber" style={{ width: `${preProb.p_draw * 100}%` }} />
          <div className="bg-accent-red" style={{ width: `${preProb.p_away * 100}%` }} />
        </div>
      ) : null}

      <Button
        variant="secondary"
        size="md"
        onClick={() => onAnalyse?.(home_team.name, away_team.name, fixture.id)}
      >
        Analyse
      </Button>
    </motion.div>
  );
}

function TeamSide({ team, side }: { team: { name: string; crest?: string | null; tla?: string | null }; side: "home" | "away" }) {
  return (
    <div className={`flex-1 flex items-center gap-2 ${side === "away" ? "flex-row-reverse text-right" : ""}`}>
      {team.crest ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={team.crest} alt="" className="w-9 h-9 object-contain" />
      ) : (
        <div className="w-9 h-9 grid place-items-center rounded-md bg-bg-tertiary text-xs font-mono">
          {team.tla || team.name.slice(0, 3).toUpperCase()}
        </div>
      )}
      <div className="text-sm font-semibold leading-tight truncate">{team.name}</div>
    </div>
  );
}
