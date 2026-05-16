"use client";
import { useEffect, useState } from "react";
import useSWR from "swr";
import clsx from "clsx";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Badge } from "@/components/ui/Badge";
import { api, getSessionId } from "@/lib/api";

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HistoryPage() {
  const [sessionId, setSessionId] = useState<string>("ssr");
  useEffect(() => setSessionId(getSessionId()), []);

  const { data, isLoading } = useSWR(
    sessionId !== "ssr" ? ["history", sessionId] : null,
    () => api.history(sessionId, 200),
  );

  const total = data?.total ?? 0;
  const correct = data?.correct ?? 0;
  const acc = data?.accuracy ?? null;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-wider uppercase">
          Your <span className="text-accent-green">Predictions</span>
        </h1>
        <p className="text-ink-muted text-sm mt-1">
          Every prediction made in this browser session, with resolved accuracy when fixtures have been played.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Accuracy</CardTitle>
          <span className="text-xs text-ink-muted uppercase tracking-widest">Resolved predictions only</span>
        </CardHeader>
        <div className="flex items-baseline gap-6">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-ink-muted">Hit rate</div>
            <div className="font-display text-5xl text-accent-green">
              {acc != null ? `${(acc * 100).toFixed(0)}%` : "—"}
            </div>
          </div>
          <div className="text-sm text-ink-muted">
            {correct} correct out of {total} resolved
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All predictions</CardTitle>
          <Badge tone="outline">{data?.rows.length ?? 0}</Badge>
        </CardHeader>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 rounded-md" />
            ))}
          </div>
        ) : !data?.rows.length ? (
          <p className="text-sm text-ink-muted">
            No predictions yet. Generate one on the home page and it will appear here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[11px] uppercase tracking-widest text-ink-muted">
                <tr className="border-b border-line">
                  <th className="text-left py-2 pl-2">Date</th>
                  <th className="text-left py-2">Match</th>
                  <th className="text-left py-2">Pick</th>
                  <th className="text-right py-2 px-1">P(H)</th>
                  <th className="text-right py-2 px-1">P(D)</th>
                  <th className="text-right py-2 px-1">P(A)</th>
                  <th className="text-left py-2 px-1">Actual</th>
                  <th className="text-right py-2 pr-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.id} className="border-b border-line/40">
                    <td className="py-2 pl-2 text-ink-muted font-mono text-xs">{fmt(r.created_at)}</td>
                    <td className="py-2">
                      <span className="font-semibold">{r.home_team}</span>
                      <span className="text-ink-muted"> vs </span>
                      <span className="font-semibold">{r.away_team}</span>
                    </td>
                    <td className="py-2">
                      <Badge
                        tone={r.predicted_outcome === "HOME" ? "green" : r.predicted_outcome === "DRAW" ? "amber" : "red"}
                      >
                        {r.predicted_outcome}
                      </Badge>
                    </td>
                    <td className="text-right font-mono px-1">{(r.p_home * 100).toFixed(0)}%</td>
                    <td className="text-right font-mono px-1">{(r.p_draw * 100).toFixed(0)}%</td>
                    <td className="text-right font-mono px-1">{(r.p_away * 100).toFixed(0)}%</td>
                    <td className="py-2 px-1">
                      {r.actual_outcome ? (
                        <span className="font-mono text-xs">
                          {r.actual_outcome}
                          {r.actual_home_goals != null && r.actual_away_goals != null
                            ? ` (${r.actual_home_goals}-${r.actual_away_goals})`
                            : ""}
                        </span>
                      ) : (
                        <span className="text-ink-muted text-xs">pending</span>
                      )}
                    </td>
                    <td className="text-right pr-2">
                      {r.correct == null ? (
                        <span className="text-ink-muted">—</span>
                      ) : r.correct ? (
                        <span className={clsx("text-accent-green font-bold")}>✓</span>
                      ) : (
                        <span className="text-accent-red font-bold">✗</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
