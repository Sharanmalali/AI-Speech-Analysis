"use client";

import { motion } from "framer-motion";
import { AlertCircle, TrendingDown, TrendingUp } from "lucide-react";

import type { FeatureContribution } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ExplainabilityPanelProps {
  contributions: FeatureContribution[];
  isAtypical: boolean;
}

export function ExplainabilityPanel({ contributions, isAtypical }: ExplainabilityPanelProps) {
  if (!contributions || contributions.length === 0) {
    return null;
  }

  // Find max absolute contribution for scaling bars
  const maxContribution = Math.max(...contributions.map((c) => Math.abs(c.contribution)));

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
      <div className="mb-3 flex items-center gap-2 text-amber-600 dark:text-amber-400">
        <AlertCircle className="h-4 w-4" />
        <span className="text-xs font-semibold uppercase tracking-wide">
          Why {isAtypical ? "Atypical" : "Typical"}?
        </span>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Top factors influencing the atypicality assessment:
      </p>

      <div className="space-y-2.5">
        {contributions.map((contrib, idx) => {
          const isTowardsAtypical = contrib.contribution > 0;
          const barWidth = (Math.abs(contrib.contribution) / maxContribution) * 100;
          const directionIcon =
            contrib.direction === "high" ? (
              <TrendingUp className="h-3 w-3" />
            ) : contrib.direction === "low" ? (
              <TrendingDown className="h-3 w-3" />
            ) : null;

          return (
            <motion.div
              key={contrib.feature}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="space-y-1"
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="font-medium">{contrib.display_name}</span>
                  {directionIcon && (
                    <span
                      className={cn(
                        "inline-flex items-center",
                        contrib.direction === "high"
                          ? "text-red-500"
                          : contrib.direction === "low"
                            ? "text-blue-500"
                            : "text-muted-foreground",
                      )}
                    >
                      {directionIcon}
                    </span>
                  )}
                </div>
                <span className="tabular-nums text-muted-foreground">
                  {contrib.value.toFixed(3)}
                </span>
              </div>
              <div className="relative h-2 overflow-hidden rounded-full bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${barWidth}%` }}
                  transition={{ duration: 0.6, delay: idx * 0.05 }}
                  className={cn(
                    "h-full rounded-full",
                    isTowardsAtypical
                      ? "bg-gradient-to-r from-red-500 to-red-600"
                      : "bg-gradient-to-r from-emerald-500 to-emerald-600",
                  )}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-4 border-t border-amber-500/20 pt-3 text-[10px] text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-gradient-to-r from-red-500 to-red-600" />
          <span>Towards Atypical</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600" />
          <span>Towards Typical</span>
        </div>
      </div>
    </div>
  );
}
