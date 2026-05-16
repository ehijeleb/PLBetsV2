"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";

import { Badge } from "./ui/Badge";

const LINKS = [
  { href: "/", label: "Predict" },
  { href: "/stats", label: "Stats" },
  { href: "/history", label: "History" },
];

export function Nav() {
  const pathname = usePathname();
  const [now, setNow] = useState<string>("");
  const [gw, setGw] = useState<number | null>(null);

  useEffect(() => {
    const t = setInterval(() => {
      const d = new Date();
      // Format in the user's local TZ but label as UK if they're not in the UK — the brief asks
      // for "UK time" but this UX is friendlier than silently shifting the clock for non-UK users.
      const ukTime = d.toLocaleTimeString("en-GB", {
        timeZone: "Europe/London",
        hour: "2-digit",
        minute: "2-digit",
      });
      setNow(ukTime);
    }, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    // Best-effort GW number from the first upcoming fixture.
    let cancelled = false;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/fixtures/upcoming?limit=1`)
      .then((r) => (r.ok ? r.json() : { fixtures: [] }))
      .then((j) => {
        if (!cancelled && j?.fixtures?.[0]?.matchday) setGw(j.fixtures[0].matchday);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-bg-primary/70 border-b border-line">
      <div className="max-w-7xl mx-auto px-5 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <span className="font-display text-2xl tracking-widest text-accent-green">PL</span>
            <span className="font-display text-xl tracking-widest text-ink">BETS</span>
          </Link>
          {gw ? <Badge tone="green">GW {gw}</Badge> : null}
        </div>

        <nav className="hidden sm:flex items-center gap-1">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-md uppercase tracking-widest font-display",
                pathname === l.href
                  ? "bg-bg-tertiary text-accent-green"
                  : "text-ink-muted hover:text-ink",
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3 text-xs text-ink-muted">
          <span className="live-dot w-1.5 h-1.5 rounded-full bg-accent-green inline-block" />
          <span className="font-mono">UK · {now}</span>
        </div>
      </div>
    </header>
  );
}
