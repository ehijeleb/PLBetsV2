"use client";
import { motion } from "framer-motion";

interface ProbabilityBarProps {
  pHome: number;
  pDraw: number;
  pAway: number;
  homeName: string;
  awayName: string;
}

export function ProbabilityBar({ pHome, pDraw, pAway, homeName, awayName }: ProbabilityBarProps) {
  return (
    <div className="space-y-4">
      <Row
        label={`${homeName} win`}
        pct={pHome}
        color="bg-accent-green"
        textColor="text-accent-green"
        side="L"
      />
      <Row label="Draw" pct={pDraw} color="bg-accent-amber" textColor="text-accent-amber" side="L" />
      <Row
        label={`${awayName} win`}
        pct={pAway}
        color="bg-accent-red"
        textColor="text-accent-red"
        side="L"
      />
    </div>
  );
}

function Row({
  label,
  pct,
  color,
  textColor,
  side,
}: {
  label: string;
  pct: number;
  color: string;
  textColor: string;
  side: "L" | "R";
}) {
  const wPct = Math.max(0, Math.min(1, pct)) * 100;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="font-display tracking-widest text-sm uppercase text-ink-muted">{label}</span>
        <span className={`font-mono text-lg font-semibold ${textColor}`}>{wPct.toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-bg-tertiary rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${wPct}%` }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
