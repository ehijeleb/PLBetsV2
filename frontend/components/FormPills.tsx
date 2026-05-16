import clsx from "clsx";
import type { ResultLetter, TeamForm } from "@/lib/types";

interface FormPillsProps {
  form: TeamForm;
  side: "home" | "away";
}

const COLOR: Record<ResultLetter, string> = {
  W: "bg-accent-green text-bg-primary",
  D: "bg-accent-amber text-bg-primary",
  L: "bg-accent-red text-bg-primary",
};

export function FormPills({ form, side }: FormPillsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h4 className="font-display tracking-wider text-base uppercase">
          {form.team}
          <span className="ml-2 text-ink-muted text-xs font-mono">{side === "home" ? "(home form)" : "(away form)"}</span>
        </h4>
      </div>
      <div className="flex gap-1.5">
        {form.matches.map((m, i) => (
          <span
            key={i}
            title={`${m.opponent} ${m.goals_for}-${m.goals_against} (${m.venue})`}
            className={clsx(
              "w-7 h-7 grid place-items-center rounded-md font-bold text-xs",
              COLOR[m.result],
            )}
          >
            {m.result}
          </span>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-3 text-xs">
        <Stat label="W-D-L" value={`${form.wins}-${form.draws}-${form.losses}`} />
        <Stat label="GS" value={form.goals_scored} />
        <Stat label="GC" value={form.goals_conceded} />
        <Stat label="CS" value={form.clean_sheets} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-bg-tertiary rounded-md px-2 py-1.5">
      <div className="text-[10px] uppercase text-ink-muted tracking-widest">{label}</div>
      <div className="font-mono text-sm">{value}</div>
    </div>
  );
}
