"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import useSWR from "swr";
import clsx from "clsx";

import { Button } from "./ui/Button";
import { Card, CardHeader, CardTitle } from "./ui/Card";
import { api, getSessionId } from "@/lib/api";
import type { PredictResponse } from "@/lib/types";

interface PredictionPanelProps {
  initialHome?: string;
  initialAway?: string;
  onResult?: (r: PredictResponse) => void;
}

export function PredictionPanel({ initialHome, initialAway, onResult }: PredictionPanelProps) {
  const [home, setHome] = useState(initialHome ?? "");
  const [away, setAway] = useState(initialAway ?? "");
  const [referee, setReferee] = useState<string>("");
  const [kickoffISO, setKickoffISO] = useState<string>("");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: teamsData } = useSWR("/teams", api.teams);
  const { data: refData } = useSWR("/referees", () => api.referees(20));
  const teams = teamsData?.teams ?? [];
  const referees = refData?.referees ?? [];

  useEffect(() => {
    if (initialHome) setHome(initialHome);
    if (initialAway) setAway(initialAway);
  }, [initialHome, initialAway]);

  const canSubmit =
    home.trim().length >= 2 &&
    away.trim().length >= 2 &&
    home.trim().toLowerCase() !== away.trim().toLowerCase();

  async function handleSubmit() {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.predict({
        home_team: home.trim(),
        away_team: away.trim(),
        referee: referee || undefined,
        kickoff: kickoffISO ? new Date(kickoffISO).toISOString() : undefined,
        session_id: getSessionId(),
      });
      onResult?.(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card elevated className="space-y-5">
      <CardHeader>
        <CardTitle>Generate Prediction</CardTitle>
        <span className="text-xs text-ink-muted uppercase tracking-widest">XGB · LGB · RF ensemble</span>
      </CardHeader>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] items-center gap-4">
        <TeamAutocomplete value={home} onChange={setHome} teams={teams} label="Home Team" tone="green" />
        <div className="vs-divider w-14 h-14 rounded-full grid place-items-center font-display text-2xl text-accent-green mx-auto">
          VS
        </div>
        <TeamAutocomplete value={away} onChange={setAway} teams={teams} label="Away Team" tone="red" />
      </div>

      <button
        type="button"
        onClick={() => setAdvancedOpen((v) => !v)}
        className="text-xs uppercase tracking-widest text-ink-muted hover:text-ink"
      >
        {advancedOpen ? "− Hide" : "+ Show"} advanced filters
      </button>

      {advancedOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="grid sm:grid-cols-2 gap-3 overflow-hidden"
        >
          <Field label="Referee">
            <select
              value={referee}
              onChange={(e) => setReferee(e.target.value)}
              className="w-full bg-bg-tertiary border border-line rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent-green/40"
            >
              <option value="">— Any —</option>
              {referees.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Kickoff (local)">
            <input
              type="datetime-local"
              value={kickoffISO}
              onChange={(e) => setKickoffISO(e.target.value)}
              className="w-full bg-bg-tertiary border border-line rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent-green/40"
            />
          </Field>
        </motion.div>
      )}

      <Button
        variant="primary"
        size="xl"
        fullWidth
        loading={loading}
        disabled={!canSubmit}
        onClick={handleSubmit}
      >
        {loading ? "Crunching..." : "Generate Prediction"}
      </Button>
      {error ? <p className="text-accent-red text-sm">{error}</p> : null}
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[11px] uppercase tracking-widest text-ink-muted mb-1 block">{label}</span>
      {children}
    </label>
  );
}

function TeamAutocomplete({
  value,
  onChange,
  teams,
  label,
  tone,
}: {
  value: string;
  onChange: (v: string) => void;
  teams: string[];
  label: string;
  tone: "green" | "red";
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const filtered = useMemo(() => {
    const v = value.trim().toLowerCase();
    if (!v) return teams.slice(0, 8);
    return teams.filter((t) => t.toLowerCase().includes(v)).slice(0, 8);
  }, [value, teams]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const ring =
    tone === "green"
      ? "focus:border-accent-green/50 focus:shadow-glow"
      : "focus:border-accent-red/50";

  return (
    <div ref={ref} className="relative">
      <span className="text-[11px] uppercase tracking-widest text-ink-muted mb-1 block">{label}</span>
      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder="Start typing..."
        className={clsx(
          "w-full bg-bg-tertiary border border-line rounded-lg px-3 py-3 text-base focus:outline-none transition-all",
          ring,
        )}
      />
      {open && filtered.length > 0 && (
        <div className="absolute z-20 mt-1 w-full bg-bg-secondary border border-line rounded-lg shadow-2xl overflow-hidden">
          {filtered.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => {
                onChange(t);
                setOpen(false);
              }}
              className="block w-full text-left px-3 py-2 text-sm hover:bg-bg-tertiary"
            >
              {t}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
