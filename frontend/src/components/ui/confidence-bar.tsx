import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  label: string;
  value: number | null | undefined; // 0..1
  color?: string;
  className?: string;
}

/** A labelled horizontal bar for displaying a 0–1 confidence value. */
export function ConfidenceBar({ label, value, color = "#6366F1", className }: ConfidenceBarProps) {
  const pct = value != null ? Math.round(Math.max(0, Math.min(1, value)) * 100) : null;
  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium tabular-nums">{pct != null ? `${pct}%` : "n/a"}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct ?? 0}%`, background: color }}
        />
      </div>
    </div>
  );
}
