"use client";

import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SpeakerRead } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

/* Theme-aware custom tooltip (frosted card) */
function ChartTooltip({
  active,
  payload,
  unit = "s",
}: {
  active?: boolean;
  payload?: { name: string; value: number; color?: string; payload?: { color?: string } }[];
  unit?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border/70 bg-popover/95 px-3 py-2 text-xs shadow-elevated backdrop-blur">
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 py-0.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: p.color || p.payload?.color || "hsl(var(--primary))" }}
          />
          <span className="text-muted-foreground">{p.name}</span>
          <span className="ml-auto font-semibold tabular-nums text-foreground">
            {p.value}
            {unit}
          </span>
        </div>
      ))}
    </div>
  );
}

export function SpeakingTimeChart({ speakers }: { speakers: SpeakerRead[] }) {
  const data = speakers.map((s) => ({
    name: `Speaker ${s.label}`,
    value: Number(s.total_speech_seconds.toFixed(1)),
    color: s.color || "#6366F1",
  }));
  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle className="text-base">Speaking time</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <defs>
                {data.map((d, i) => (
                  <linearGradient key={i} id={`slice-${i}`} x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={d.color} stopOpacity={0.95} />
                    <stop offset="100%" stopColor={d.color} stopOpacity={0.7} />
                  </linearGradient>
                ))}
              </defs>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={62}
                outerRadius={92}
                paddingAngle={3}
                cornerRadius={7}
                stroke="none"
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={`url(#slice-${i})`} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip unit="s" />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-2xl font-bold tracking-tight">
              {formatTimestamp(total)}
            </span>
            <span className="text-xs text-muted-foreground">total speech</span>
          </div>
        </div>

        {/* Custom legend */}
        <div className="mt-4 grid grid-cols-2 gap-2">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2 text-xs">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: d.color }} />
              <span className="truncate text-muted-foreground">{d.name}</span>
              <span className="ml-auto font-medium tabular-nums">
                {total > 0 ? Math.round((d.value / total) * 100) : 0}%
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function SpeechPauseChart({ speakers }: { speakers: SpeakerRead[] }) {
  const data = speakers.map((s) => ({
    name: `Spk ${s.label}`,
    Speech: Number(s.total_speech_seconds.toFixed(1)),
    Pauses: Number(s.total_pause_seconds.toFixed(1)),
  }));

  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle className="text-base">Speech vs. pauses</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={6} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="bar-speech" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.95} />
                  <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.55} />
                </linearGradient>
                <linearGradient id="bar-pause" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.95} />
                  <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0.55} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <Tooltip content={<ChartTooltip unit="s" />} cursor={{ fill: "hsl(var(--muted) / 0.4)" }} />
              <Bar dataKey="Speech" fill="url(#bar-speech)" radius={[7, 7, 0, 0]} maxBarSize={34} />
              <Bar dataKey="Pauses" fill="url(#bar-pause)" radius={[7, 7, 0, 0]} maxBarSize={34} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 flex items-center justify-center gap-5 text-xs">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" /> Speech
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" /> Pauses
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
