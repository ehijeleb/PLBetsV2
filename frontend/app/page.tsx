"use client";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { MatchCard } from "@/components/MatchCard";
import { PredictionPanel } from "@/components/PredictionPanel";
import { PredictionResult } from "@/components/PredictionResult";
import { api } from "@/lib/api";
import type { PredictResponse } from "@/lib/types";

export default function HomePage() {
  const { data: fixturesData, isLoading } = useSWR("/upcoming", () => api.upcomingFixtures(10));
  const fixtures = fixturesData?.fixtures ?? [];

  const [seed, setSeed] = useState<{ home: string; away: string } | undefined>();
  const [result, setResult] = useState<PredictResponse | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result) {
      // Smooth scroll to the result panel after it mounts.
      setTimeout(
        () => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        80,
      );
    }
  }, [result]);

  return (
    <div className="space-y-10">
      <section>
        <div className="flex items-baseline justify-between mb-4">
          <h1 className="font-display text-3xl sm:text-5xl tracking-wider uppercase">
            This <span className="text-accent-green">Weekend's</span> Fixtures
          </h1>
          <span className="text-xs text-ink-muted uppercase tracking-widest">
            {fixtures.length ? `${fixtures.length} scheduled` : "Live"}
          </span>
        </div>

        {isLoading ? (
          <div className="flex gap-3 overflow-x-auto pretty-scrollbar pb-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="min-w-[340px] h-32 rounded-2xl" />
            ))}
          </div>
        ) : fixtures.length === 0 ? (
          <Card>
            <p className="text-sm text-ink-muted">
              No upcoming fixtures available. The football-data.org API key is not set, or there are
              no scheduled matches in the next Premier League gameweek. Set{" "}
              <code className="font-mono text-ink">FOOTBALL_DATA_API_KEY</code> in your backend{" "}
              <code className="font-mono text-ink">.env</code> file to populate this row.
            </p>
          </Card>
        ) : (
          <div className="flex gap-3 overflow-x-auto pretty-scrollbar pb-3">
            {fixtures.map((f) => (
              <MatchCard
                key={f.id}
                fixture={f}
                onAnalyse={(home, away) => setSeed({ home, away })}
              />
            ))}
          </div>
        )}
      </section>

      <section>
        <PredictionPanel
          initialHome={seed?.home}
          initialAway={seed?.away}
          onResult={setResult}
        />
      </section>

      <div ref={resultRef}>
        {result ? <PredictionResult result={result} /> : <ResultPlaceholder />}
      </div>
    </div>
  );
}

function ResultPlaceholder() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Awaiting prediction</CardTitle>
      </CardHeader>
      <p className="text-sm text-ink-muted">
        Pick two teams above (or click "Analyse" on an upcoming fixture) to generate a probability
        breakdown, SHAP feature importance, expected goals, and betting market context.
      </p>
    </Card>
  );
}
