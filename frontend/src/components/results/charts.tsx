"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
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

/* Theme-aware frosted tooltip used by both charts. */
function ChartTooltip({
  active,
  payload,
  label,
  unit = "s",
  showPct,
}: {
  active?: boolean;
  label?: string;
  unit?: string;
  showPct?: number; // total, when set show percentage of total
  payload?: {
    name: string;
    value: number;
    color?: string;
    payload?: { color?: string; name?: string };
  }[];
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="min-w-[140px] rounded-xl border border-border/70 bg-popover/95 px-3 py-2 text-xs shadow-elevated backdrop-blur">
      {(label || payload[0]?.payload?.name) && (
        <p className="mb-1 font-semibold text-foreground">
          {label || payload[0]?.payload?.name}
        </p>
      )}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 py-0.5">
          <span
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ background: p.color || p.payload?.color || "hsl(var(--primary))" }}
          />
          <span className="text-muted-foreground">{p.name}</span>
          <span className="ml-auto font-semibold tabular-nums text-foreground">
            {p.value}
            {unit}
            {showPct ? ` · ${Math.round((p.value / showPct) * 100)}%` : ""}
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
        <CardTitle className="text-base">Speaking time share</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative h-60">
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
                innerRadius={64}
                outerRadius={94}
                paddingAngle={data.length > 1 ? 3 : 0}
                cornerRadius={7}
                stroke="none"
                isAnimationActive
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={`url(#slice-${i})`} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip unit="s" showPct={total} />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-2xl font-bold tracking-tight">
              {formatTimestamp(total)}
            </span>
            <span className="text-xs text-muted-foreground">total speech</span>
          </div>
        </div>

        {/* Legend: colour · name · seconds · percentage */}
        <div className="mt-5 space-y-2">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2.5 text-xs">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: d.color }} />
              <span className="truncate font-medium">{d.name}</span>
              <span className="ml-auto tabular-nums text-muted-foreground">
                {formatTimestamp(d.value)}
              </span>
              <span className="w-10 text-right font-semibold tabular-nums">
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
    name: `Speaker ${s.label}`,
    Speech: Number(s.total_speech_seconds.toFixed(1)),
    Pauses: Number(s.total_pause_seconds.toFixed(1)),
  }));

  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle className="text-base">Speech vs. pauses</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={6} margin={{ top: 18, right: 12, left: 4, bottom: 4 }}>
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
              <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeOpacity={0.5} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
                dy={4}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                axisLine={false}
                tickLine={false}
                width={44}
                label={{
                  value: "Seconds",
                  angle: -90,
                  position: "insideLeft",
                  style: { fontSize: 11, fill: "hsl(var(--muted-foreground))", textAnchor: "middle" },
                }}
              />
              <Tooltip
                content={<ChartTooltip unit="s" />}
                cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                height={28}
                iconType="circle"
                iconSize={9}
                wrapperStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="Speech" fill="url(#bar-speech)" radius={[6, 6, 0, 0]} maxBarSize={38}>
                <LabelList
                  dataKey="Speech"
                  position="top"
                  formatter={(v: number) => `${v}s`}
                  style={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                />
              </Bar>
              <Bar dataKey="Pauses" fill="url(#bar-pause)" radius={[6, 6, 0, 0]} maxBarSize={38}>
                <LabelList
                  dataKey="Pauses"
                  position="top"
                  formatter={(v: number) => `${v}s`}
                  style={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
