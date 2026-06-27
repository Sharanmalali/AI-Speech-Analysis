"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Check, Loader2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { jobService } from "@/lib/services";
import type { JobStage } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES: { key: JobStage; label: string }[] = [
  { key: "uploaded", label: "Uploaded" },
  { key: "noise_reduction", label: "Noise reduction" },
  { key: "diarization", label: "Speaker diarization" },
  { key: "transcription", label: "Transcription & translation" },
  { key: "feature_extraction", label: "Feature extraction" },
  { key: "gender_prediction", label: "Gender & age prediction" },
  { key: "atypicality_classification", label: "Atypicality classification" },
  { key: "aggregation", label: "Aggregating results" },
  { key: "done", label: "Done" },
];

function stageIndex(stage: JobStage): number {
  const direct = STAGES.findIndex((s) => s.key === stage);
  if (direct >= 0) return direct;
  const fallback: Record<string, JobStage> = {
    segmentation: "transcription",
    translation: "transcription",
    age_prediction: "gender_prediction",
    report_generation: "aggregation",
  };
  return STAGES.findIndex((s) => s.key === (fallback[stage] ?? "uploaded"));
}

function ProgressRing({ value, state }: { value: number; state: string }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.max(0, Math.min(100, value)) / 100) * c;
  return (
    <div className="relative h-36 w-36">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} className="fill-none stroke-muted" strokeWidth="9" />
        <motion.circle
          cx="64"
          cy="64"
          r={r}
          className="fill-none"
          stroke="url(#ring-grad)"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={c}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" />
            <stop offset="100%" stopColor="hsl(var(--accent))" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {state === "failed" ? (
          <AlertTriangle className="h-8 w-8 text-destructive" />
        ) : state === "completed" ? (
          <Check className="h-9 w-9 text-emerald-500" />
        ) : (
          <>
            <span className="font-display text-3xl font-bold tabular-nums">{Math.round(value)}</span>
            <span className="text-xs text-muted-foreground">percent</span>
          </>
        )}
      </div>
    </div>
  );
}

export default function ProcessingPage() {
  const router = useRouter();
  const { jobId } = useParams<{ jobId: string }>();

  const { data } = useQuery({
    queryKey: ["job-status", jobId],
    queryFn: () => jobService.status(jobId),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "completed" || s === "failed" || s === "cancelled" ? false : 2000;
    },
  });

  useEffect(() => {
    if (data?.status === "completed") {
      const t = setTimeout(() => router.replace(`/dashboard/results/${jobId}`), 900);
      return () => clearTimeout(t);
    }
  }, [data?.status, jobId, router]);

  const currentIdx = data ? stageIndex(data.stage) : 0;
  const failed = data?.status === "failed";
  const completed = data?.status === "completed";

  return (
    <div className="mx-auto max-w-2xl py-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="panel relative overflow-hidden p-8 md:p-10"
      >
        <div className="absolute inset-x-0 top-0 h-40 aurora opacity-25" />

        <div className="relative flex flex-col items-center text-center">
          <ProgressRing value={data?.progress ?? 0} state={data?.status ?? "processing"} />
          <h1 className="mt-6 font-display text-2xl font-bold tracking-tight">
            {failed ? "Analysis failed" : completed ? "Analysis complete" : "Analysing your recording"}
          </h1>
          <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">
            {failed
              ? data?.error_message || "An error occurred during processing."
              : completed
                ? "Redirecting you to the results…"
                : "Longer recordings can take a few minutes. You can keep this tab open."}
          </p>
        </div>

        {!failed && (
          <ol className="relative mt-8 space-y-1">
            {STAGES.map((stage, i) => {
              const done = i < currentIdx || completed;
              const active = i === currentIdx && !completed;
              return (
                <li
                  key={stage.key}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors",
                    active && "bg-primary/[0.07]",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                      done
                        ? "bg-emerald-500/15 text-emerald-500"
                        : active
                          ? "bg-primary/15 text-primary"
                          : "bg-muted text-muted-foreground",
                    )}
                  >
                    {done ? (
                      <Check className="h-4 w-4" />
                    ) : active ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      i + 1
                    )}
                  </span>
                  <span
                    className={cn(
                      "text-sm",
                      done || active ? "font-medium text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {stage.label}
                  </span>
                  {active && (
                    <span className="ml-auto text-[11px] font-medium text-primary">In progress</span>
                  )}
                </li>
              );
            })}
          </ol>
        )}

        {failed && (
          <div className="relative mt-8 flex justify-center">
            <Button variant="gradient" onClick={() => router.push("/dashboard/upload")}>
              Try another file <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
