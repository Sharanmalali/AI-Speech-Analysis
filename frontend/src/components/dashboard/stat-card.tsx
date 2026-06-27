import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  icon: LucideIcon;
  accent?: "primary" | "emerald" | "amber" | "rose" | "sky";
  className?: string;
}

const ACCENTS: Record<NonNullable<StatCardProps["accent"]>, string> = {
  primary: "from-indigo-500/15 to-violet-500/15 text-indigo-500",
  emerald: "from-emerald-500/15 to-teal-500/15 text-emerald-500",
  amber: "from-amber-500/15 to-orange-500/15 text-amber-500",
  rose: "from-rose-500/15 to-pink-500/15 text-rose-500",
  sky: "from-sky-500/15 to-cyan-500/15 text-sky-500",
};

/** A compact KPI tile used across dashboards. */
export function StatCard({ label, value, hint, icon: Icon, accent = "primary", className }: StatCardProps) {
  return (
    <div className={cn("panel panel-hover flex items-center gap-4 p-5", className)}>
      <div
        className={cn(
          "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br",
          ACCENTS[accent],
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          {label}
        </p>
        <div className="font-display text-2xl font-bold leading-tight tracking-tight">{value}</div>
        {hint && <p className="truncate text-xs text-muted-foreground">{hint}</p>}
      </div>
    </div>
  );
}
