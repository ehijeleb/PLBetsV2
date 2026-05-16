import clsx from "clsx";
import type { StandingRow } from "@/lib/types";

interface LeagueTableProps {
  rows: StandingRow[];
}

export function LeagueTable({ rows }: LeagueTableProps) {
  if (!rows?.length) {
    return <p className="text-ink-muted text-sm">No standings available — set FOOTBALL_DATA_API_KEY to populate.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-[11px] uppercase tracking-widest text-ink-muted">
          <tr className="border-b border-line">
            <th className="text-left py-2 pl-2">#</th>
            <th className="text-left py-2">Team</th>
            <th className="text-right py-2 px-1">P</th>
            <th className="text-right py-2 px-1">W</th>
            <th className="text-right py-2 px-1">D</th>
            <th className="text-right py-2 px-1">L</th>
            <th className="text-right py-2 px-1">GF</th>
            <th className="text-right py-2 px-1">GA</th>
            <th className="text-right py-2 px-1">GD</th>
            <th className="text-right py-2 px-2">Pts</th>
            <th className="text-left py-2 pl-3">Form</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.team.id} className="border-b border-line/40 hover:bg-bg-tertiary/40 transition-colors">
              <td className="py-2 pl-2 font-mono text-ink-muted">{r.position}</td>
              <td className="py-2">
                <div className="flex items-center gap-2">
                  {r.team.crest ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={r.team.crest} alt="" className="w-5 h-5 object-contain" />
                  ) : (
                    <span className="w-5 h-5 inline-block bg-bg-tertiary rounded-sm" />
                  )}
                  <span className="font-semibold">{r.team.name}</span>
                </div>
              </td>
              <td className="text-right font-mono px-1">{r.played}</td>
              <td className="text-right font-mono px-1">{r.won}</td>
              <td className="text-right font-mono px-1">{r.draw}</td>
              <td className="text-right font-mono px-1">{r.lost}</td>
              <td className="text-right font-mono px-1">{r.goals_for}</td>
              <td className="text-right font-mono px-1">{r.goals_against}</td>
              <td className={clsx("text-right font-mono px-1", r.goal_difference >= 0 ? "text-accent-green" : "text-accent-red")}>
                {r.goal_difference > 0 ? "+" : ""}
                {r.goal_difference}
              </td>
              <td className="text-right font-mono font-bold px-2">{r.points}</td>
              <td className="pl-3">
                {r.form ? (
                  <span className="font-mono text-xs">
                    {r.form.split(",").slice(-5).map((c, i) => {
                      const k = c.trim();
                      const cls =
                        k === "W"
                          ? "text-accent-green"
                          : k === "D"
                            ? "text-accent-amber"
                            : "text-accent-red";
                      return (
                        <span key={i} className={`mr-0.5 ${cls}`}>
                          {k}
                        </span>
                      );
                    })}
                  </span>
                ) : (
                  <span className="text-ink-muted">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
