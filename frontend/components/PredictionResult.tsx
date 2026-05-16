"use client";
import { motion } from "framer-motion";

import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { ProbabilityBar } from "./ProbabilityBar";
import { ShapChart } from "./ShapChart";
import { FormPills } from "./FormPills";
import { H2HTimeline } from "./H2HTimeline";
import { BettingInsightBox } from "./BettingInsightBox";
import type { PredictResponse } from "@/lib/types";

interface PredictionResultProps {
  result: PredictResponse;
}

const BAND_TONE = { LOW: "amber", MEDIUM: "amber", HIGH: "green" } as const;

export function PredictionResult({ result }: PredictionResultProps) {
  const predictedName =
    result.predicted_outcome === "HOME"
      ? result.home_team
      : result.predicted_outcome === "AWAY"
        ? result.away_team
        : "Draw";

  async function copy() {
    const lines = [
      `PLBets v2 — Prediction`,
      `${result.home_team} vs ${result.away_team}`,
      `HOME ${(result.p_home * 100).toFixed(1)}% · DRAW ${(result.p_draw * 100).toFixed(1)}% · AWAY ${(result.p_away * 100).toFixed(1)}%`,
      `Pick: ${predictedName} (confidence ${result.confidence_band}, ${(result.confidence * 100).toFixed(1)}%)`,
      `xG: ${result.goal_markets.expected_home_goals.toFixed(2)} – ${result.goal_markets.expected_away_goals.toFixed(2)}`,
      `BTTS ${(result.goal_markets.p_btts * 100).toFixed(1)}% · O2.5 ${(result.goal_markets.p_over_25 * 100).toFixed(1)}%`,
    ];
    await navigator.clipboard.writeText(lines.join("\n"));
  }

  return (
    <motion.section
      id="prediction-result"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <Card elevated>
        <CardHeader>
          <div>
            <CardTitle>
              {result.home_team} <span className="text-ink-muted">vs</span> {result.away_team}
            </CardTitle>
            <p className="text-xs text-ink-muted mt-1 uppercase tracking-widest">Outcome probabilities</p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge tone={BAND_TONE[result.confidence_band]}>
              {result.confidence_band} CONFIDENCE
            </Badge>
            <span className="text-xs font-mono text-ink-muted">
              {(result.confidence * 100).toFixed(1)}% probability
            </span>
          </div>
        </CardHeader>

        <ProbabilityBar
          pHome={result.p_home}
          pDraw={result.p_draw}
          pAway={result.p_away}
          homeName={result.home_team}
          awayName={result.away_team}
        />

        <div className="mt-6 flex items-center justify-between gap-4 bg-bg-tertiary rounded-xl p-4">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-ink-muted">Model prediction</div>
            <div className="font-display tracking-wide text-2xl mt-1">★ {predictedName}</div>
          </div>
          <Button variant="ghost" size="sm" onClick={copy}>
            Copy summary
          </Button>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Why this prediction?</CardTitle>
          <span className="text-xs text-ink-muted uppercase tracking-widest">Top 5 SHAP features</span>
        </CardHeader>
        <ShapChart features={result.shap_top} />
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {result.home_form ? (
          <Card>
            <CardHeader>
              <CardTitle>Home form</CardTitle>
            </CardHeader>
            <FormPills form={result.home_form} side="home" />
          </Card>
        ) : null}
        {result.away_form ? (
          <Card>
            <CardHeader>
              <CardTitle>Away form</CardTitle>
            </CardHeader>
            <FormPills form={result.away_form} side="away" />
          </Card>
        ) : null}
      </div>

      {result.h2h ? (
        <Card>
          <CardHeader>
            <CardTitle>Head-to-head</CardTitle>
          </CardHeader>
          <H2HTimeline h2h={result.h2h} />
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Betting insight</CardTitle>
          <span className="text-xs text-ink-muted uppercase tracking-widest">Markets implied by model</span>
        </CardHeader>
        <BettingInsightBox
          homeName={result.home_team}
          awayName={result.away_team}
          predictedOutcome={result.predicted_outcome}
          pHome={result.p_home}
          pDraw={result.p_draw}
          pAway={result.p_away}
          goalMarkets={result.goal_markets}
        />
      </Card>
    </motion.section>
  );
}
