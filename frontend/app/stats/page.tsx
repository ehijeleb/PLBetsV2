"use client";
import useSWR from "swr";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { LeagueTable } from "@/components/LeagueTable";
import { FormHeatmap } from "@/components/FormHeatmap";
import { HomeVsAwayChart } from "@/components/HomeVsAwayChart";
import { api } from "@/lib/api";

export default function StatsPage() {
  const { data: standings, isLoading: standingsLoading } = useSWR("/standings", api.standings);
  const { data: heatmap, isLoading: heatmapLoading } = useSWR("/heatmap", () => api.formHeatmap(10));
  const { data: hva, isLoading: hvaLoading } = useSWR("/hva", api.homeVsAway);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-wider uppercase">
          Premier League <span className="text-accent-green">Stats Hub</span>
        </h1>
        <p className="text-ink-muted text-sm mt-1">League table, recent form heatmap, and home-vs-away splits.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>League Table</CardTitle>
          <span className="text-xs text-ink-muted uppercase tracking-widest">Live via football-data.org</span>
        </CardHeader>
        {standingsLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-8 rounded-md" />
            ))}
          </div>
        ) : (
          <LeagueTable rows={standings?.rows ?? []} />
        )}
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Form heatmap</CardTitle>
            <span className="text-xs text-ink-muted uppercase tracking-widest">Last 10 matches</span>
          </CardHeader>
          {heatmapLoading ? <Skeleton className="h-80 rounded-lg" /> : <FormHeatmap teams={heatmap?.teams ?? []} />}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Home vs Away</CardTitle>
            <span className="text-xs text-ink-muted uppercase tracking-widest">Win rate, this season</span>
          </CardHeader>
          {hvaLoading ? <Skeleton className="h-96 rounded-lg" /> : <HomeVsAwayChart teams={hva?.teams ?? []} />}
        </Card>
      </div>
    </div>
  );
}
