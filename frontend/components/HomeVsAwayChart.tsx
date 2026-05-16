"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import type { HomeVsAwayTeam } from "@/lib/types";

export function HomeVsAwayChart({ teams }: { teams: HomeVsAwayTeam[] }) {
  if (!teams.length) return <p className="text-ink-muted text-sm">No data available.</p>;

  const data = teams.map((t) => ({
    team: t.team,
    Home: Math.round(t.home_win_rate * 100),
    Away: Math.round(t.away_win_rate * 100),
  }));

  return (
    <div style={{ width: "100%", height: 460 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 24, right: 16, top: 8, bottom: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" stroke="var(--text-muted)" fontSize={11} unit="%" />
          <YAxis dataKey="team" type="category" stroke="var(--text-muted)" fontSize={11} width={120} interval={0} />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            contentStyle={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--text-primary)",
              fontSize: 12,
            }}
            formatter={(v: number) => [`${v}%`, ""]}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }} />
          <Bar dataKey="Home" fill="var(--accent-green)" radius={[0, 4, 4, 0]} />
          <Bar dataKey="Away" fill="var(--accent-red)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
