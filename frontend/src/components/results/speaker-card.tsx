"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ConfidenceBar } from "@/components/ui/confidence-bar";
import type { SpeakerRead } from "@/lib/types";
import { cn, formatTimestamp, titleCase } from "@/lib/utils";

export function SpeakerCard({ speaker, index }: { speaker: SpeakerRead; index: number }) {
  const p = speaker.prediction;
  const atypical = p?.atypicality === "atypical";
  const color = speaker.color || "#6366F1";
  const viaAI = p?.gender_age_source === "llm" || p?.gender_age_source === "hf";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      className="panel overflow-hidden"
    >
      <div className="h-1.5 w-full" style={{ background: color }} />
      <div className="space-y-4 p-5">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <div
              className="flex h-11 w-11 items-center justify-center rounded-xl text-base font-bold text-white shadow-sm"
              style={{ background: color }}
            >
              {speaker.label}
            </div>
            <div>
              <p className="font-semibold leading-tight">Speaker {speaker.label}</p>
              <p className="text-xs text-muted-foreground">
                {speaker.segment_count} segments · {speaker.word_count} words
              </p>
            </div>
          </div>
          <Badge variant={atypical ? "destructive" : "success"}>
            {p ? titleCase(p.atypicality) : "Unknown"}
          </Badge>
        </div>

        {/* Gender / age */}
        <div className="rounded-xl bg-muted/40 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-semibold">{p ? titleCase(p.gender) : "—"}</span>
              <span className="text-xs text-muted-foreground">·</span>
              <span className="text-sm font-semibold">{p ? titleCase(p.age_group) : "—"}</span>
            </div>
            {viaAI && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                <Sparkles className="h-3 w-3" /> AI
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <ConfidenceBar label="Gender" value={p?.gender_confidence} color={color} />
            <ConfidenceBar label="Age" value={p?.age_confidence} color={color} />
          </div>
        </div>

        {/* Speech stats */}
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Speech" value={formatTimestamp(speaker.total_speech_seconds)} />
          <Stat label="Pauses" value={formatTimestamp(speaker.total_pause_seconds)} />
        </div>

        {/* Atypicality detail */}
        {p?.atypicality_score != null && (
          <div
            className={cn(
              "rounded-xl border p-3 text-xs",
              atypical
                ? "border-destructive/20 bg-destructive/5 text-destructive"
                : "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400",
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">Atypicality score</span>
              <span className="font-bold tabular-nums">{p.atypicality_score.toFixed(3)}</span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-muted/40 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-semibold tabular-nums">{value}</p>
    </div>
  );
}
