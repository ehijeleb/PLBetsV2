"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer, ReferenceLine } from "recharts";
import type { ShapFeature } from "@/lib/types";

interface ShapChartProps {
  features: ShapFeature[];
}

const COLOR_FOR = (c: ShapFeature["contribution"]) => {
  switch (c) {
    case "home":
      return "var(--accent-green)";
    case "away":
      return "var(--accent-red)";
    default:
      return "var(--accent-amber)";
  }
};

export function ShapChart({ features }: ShapChartProps) {
  if (!features?.length) {
    return <p className="text-ink-muted text-sm">No SHAP values returned.</p>;
  }
  const data = features
    .map((f) => ({
      label: f.label,
      value: Number(f.shap_value.toFixed(3)),
      color: COLOR_FOR(f.contribution),
      contribution: f.contribution,
    }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  return (
    <div style={{ width: "100%", height: 240 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
          <YAxis
            type="category"
            dataKey="label"
            stroke="var(--text-muted)"
            fontSize={11}
            width={220}
            interval={0}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            contentStyle={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--text-primary)",
              fontSize: 12,
            }}
            formatter={(v: number) => [v.toFixed(3), "SHAP value"]}
          />
          <ReferenceLine x={0} stroke="var(--border)" />
          <Bar dataKey="value" radius={[2, 6, 6, 2]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
