import clsx from "clsx";
import { HTMLAttributes } from "react";

type Tone = "green" | "amber" | "red" | "neutral" | "outline";

const TONES: Record<Tone, string> = {
  green: "bg-accent-green/15 text-accent-green border-accent-green/30",
  amber: "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  red: "bg-accent-red/15 text-accent-red border-accent-red/30",
  neutral: "bg-bg-tertiary text-ink-muted border-line",
  outline: "bg-transparent text-ink border-line",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
  mono?: boolean;
}

export function Badge({ tone = "neutral", mono, className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider rounded-md border",
        TONES[tone],
        mono && "font-mono",
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
