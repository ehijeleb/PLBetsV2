import clsx from "clsx";
import type { FormHeatmapTeam, ResultLetter } from "@/lib/types";

const COLOR: Record<ResultLetter, string> = {
  W: "bg-accent-green",
  D: "bg-accent-amber",
  L: "bg-accent-red",
};

export function FormHeatmap({ teams }: { teams: FormHeatmapTeam[] }) {
  if (!teams.length) {
    return <p className="text-ink-muted text-sm">No form data available.</p>;
  }
  return (
    <div className="space-y-2">
      {teams.map((t) => (
        <div key={t.team} className="grid grid-cols-[160px_1fr] items-center gap-3">
          <div className="text-sm truncate">{t.team}</div>
          <div className="flex gap-1">
            {t.results.map((r, i) => (
              <span
                key={i}
                title={r}
                className={clsx("w-5 h-5 rounded-sm grid place-items-center text-[10px] text-bg-primary font-bold", COLOR[r])}
              >
                {r}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
