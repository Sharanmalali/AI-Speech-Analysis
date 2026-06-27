"use client";

import {
  motion,
  useMotionValue,
  useReducedMotion,
  useSpring,
  useTransform,
} from "framer-motion";
import {
  Activity,
  AudioWaveform,
  Brain,
  ChevronRight,
  Database,
  FileText,
  Languages,
  type LucideIcon,
  Mic,
  Scissors,
  Upload,
  UserCheck,
  Users,
} from "lucide-react";
import { Fragment, useEffect, useState } from "react";

type Stage = { icon: LucideIcon; label: string; hint: string };
type Phase = {
  name: string;
  badge: string;
  dot: string;
  text: string;
  glow: string;
  depth: number;
  stages: Stage[];
};

/* The pipeline mirrors the AUDIO PROCESSING PIPELINE in the workflow chart,
   grouped into five readable phases so judges follow the full flow at a glance. */
const PHASES: Phase[] = [
  {
    name: "Ingest",
    badge: "bg-sky-500/12 text-sky-600 dark:text-sky-300",
    dot: "bg-sky-500",
    text: "text-sky-600 dark:text-sky-300",
    glow: "shadow-[0_0_28px_-6px_rgba(14,165,233,0.55)] ring-sky-500/50",
    depth: 0,
    stages: [
      { icon: Upload, label: "Upload audio", hint: "wav · mp3 · m4a · ogg" },
      { icon: AudioWaveform, label: "Noise reduction", hint: "clean + standardise 16 kHz" },
    ],
  },
  {
    name: "Separate",
    badge: "bg-indigo-500/12 text-indigo-600 dark:text-indigo-300",
    dot: "bg-indigo-500",
    text: "text-indigo-600 dark:text-indigo-300",
    glow: "shadow-[0_0_28px_-6px_rgba(99,102,241,0.6)] ring-indigo-500/50",
    depth: 22,
    stages: [
      { icon: Users, label: "Speaker diarization", hint: "who spoke when · PyAnnote" },
      { icon: Scissors, label: "Segmentation", hint: "per-speaker turns" },
    ],
  },
  {
    name: "Understand",
    badge: "bg-violet-500/12 text-violet-600 dark:text-violet-300",
    dot: "bg-violet-500",
    text: "text-violet-600 dark:text-violet-300",
    glow: "shadow-[0_0_28px_-6px_rgba(139,92,246,0.6)] ring-violet-500/50",
    depth: 34,
    stages: [
      { icon: Mic, label: "Kannada speech → text", hint: "Whisper ASR" },
      { icon: Languages, label: "Translate → English", hint: "timestamped turns" },
    ],
  },
  {
    name: "Analyze",
    badge: "bg-rose-500/12 text-rose-600 dark:text-rose-300",
    dot: "bg-rose-500",
    text: "text-rose-600 dark:text-rose-300",
    glow: "shadow-[0_0_28px_-6px_rgba(244,63,94,0.55)] ring-rose-500/50",
    depth: 22,
    stages: [
      { icon: Activity, label: "Acoustic features", hint: "Librosa · Parselmouth" },
      { icon: UserCheck, label: "Gender & age", hint: "wav2vec2 models" },
      { icon: Brain, label: "Typical / Atypical", hint: "screening model" },
    ],
  },
  {
    name: "Deliver",
    badge: "bg-emerald-500/12 text-emerald-600 dark:text-emerald-300",
    dot: "bg-emerald-500",
    text: "text-emerald-600 dark:text-emerald-300",
    glow: "shadow-[0_0_28px_-6px_rgba(16,185,129,0.55)] ring-emerald-500/50",
    depth: 0,
    stages: [
      { icon: Database, label: "Combine & store", hint: "Supabase Postgres" },
      { icon: FileText, label: "PDF report", hint: "clinical, downloadable" },
    ],
  },
];

const TOTAL = PHASES.reduce((n, p) => n + p.stages.length, 0);
const PHASE_OFFSETS = PHASES.reduce<number[]>((acc, p, i) => {
  acc.push((acc[i - 1] ?? 0) + (i === 0 ? 0 : PHASES[i - 1].stages.length));
  return acc;
}, []);

export function Workflow3D() {
  const reduced = useReducedMotion();
  const [active, setActive] = useState(0);

  // Traveling "data pulse" that lights up each stage in sequence to
  // demonstrate the direction of flow through the pipeline.
  useEffect(() => {
    if (reduced) return;
    const id = setInterval(() => setActive((a) => (a + 1) % TOTAL), 1100);
    return () => clearInterval(id);
  }, [reduced]);

  // Mouse-driven 3D parallax (desktop / fine pointers only).
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-11, 11]), {
    stiffness: 120,
    damping: 18,
  });
  const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [8, -8]), {
    stiffness: 120,
    damping: 18,
  });

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    if (reduced) return;
    const r = e.currentTarget.getBoundingClientRect();
    mx.set((e.clientX - r.left) / r.width - 0.5);
    my.set((e.clientY - r.top) / r.height - 0.5);
  }
  function onLeave() {
    mx.set(0);
    my.set(0);
  }

  return (
    <div className="relative">
      {/* Ambient depth backdrop */}
      <div className="pointer-events-none absolute inset-0 -z-10 aurora opacity-60 blur-2xl" />
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-[0.35]" />

      <div
        className="mx-auto max-w-6xl [perspective:1800px]"
        onMouseMove={onMove}
        onMouseLeave={onLeave}
      >
        <motion.div
          style={{ rotateX: reduced ? 0 : rotateX, rotateY: reduced ? 0 : rotateY, transformStyle: "preserve-3d" }}
          className="flex flex-col gap-6 lg:flex-row lg:items-stretch lg:gap-2"
        >
          {PHASES.map((phase, pi) => (
            <Fragment key={phase.name}>
              <motion.div
                initial={{ opacity: 0, y: 26 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.5, delay: pi * 0.08, ease: [0.22, 1, 0.36, 1] }}
                style={{ transform: `translateZ(${phase.depth}px)`, transformStyle: "preserve-3d" }}
                className="flex-1"
              >
                {/* Phase header */}
                <div className="mb-3 flex items-center gap-2">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-lg text-[11px] font-bold ${phase.badge}`}>
                    {pi + 1}
                  </span>
                  <span className="text-sm font-semibold">{phase.name}</span>
                </div>

                <div className="space-y-3">
                  {phase.stages.map((stage, si) => {
                    const idx = PHASE_OFFSETS[pi] + si;
                    const isActive = !reduced && idx === active;
                    return (
                      <motion.div
                        key={stage.label}
                        animate={
                          reduced
                            ? undefined
                            : { translateZ: isActive ? 46 : 0, scale: isActive ? 1.035 : 1 }
                        }
                        transition={{ type: "spring", stiffness: 260, damping: 20 }}
                        className={`group relative rounded-2xl border bg-card/90 p-3.5 backdrop-blur transition-colors ${
                          isActive
                            ? `border-transparent ring-2 ${phase.glow}`
                            : "border-border/70 shadow-soft hover:border-primary/30"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${phase.badge}`}
                          >
                            <stage.icon className="h-4.5 w-4.5" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-sm font-semibold leading-tight">{stage.label}</p>
                            <p className="mt-0.5 truncate text-xs text-muted-foreground">{stage.hint}</p>
                          </div>
                        </div>
                        {/* active pulse dot */}
                        {isActive && (
                          <span className="absolute -right-1 -top-1 flex h-3 w-3">
                            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-70 ${phase.dot}`} />
                            <span className={`relative inline-flex h-3 w-3 rounded-full ${phase.dot}`} />
                          </span>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>

              {/* Connector between phases */}
              {pi < PHASES.length - 1 && (
                <div
                  className="flex shrink-0 items-center justify-center lg:flex-col"
                  style={{ transform: `translateZ(${Math.max(phase.depth, PHASES[pi + 1].depth)}px)` }}
                >
                  <Connector vertical />
                </div>
              )}
            </Fragment>
          ))}
        </motion.div>
      </div>

      {/* Caption / legend */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-70" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
          </span>
          Live data flow
        </span>
        <span>{TOTAL} processing stages · 5 phases</span>
        <span className="hidden sm:inline">Move your cursor to explore in 3D</span>
      </div>
    </div>
  );
}

function Connector({ vertical }: { vertical?: boolean }) {
  return (
    <div className={`relative ${vertical ? "h-6 w-px lg:h-px lg:w-6" : "h-px w-6"}`}>
      <div className="absolute inset-0 rounded-full bg-gradient-to-r from-primary/40 via-accent/40 to-primary/40 lg:bg-gradient-to-b" />
      <motion.span
        aria-hidden
        className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-[0_0_8px_2px_rgba(139,92,246,0.6)]"
        animate={{ opacity: [0.2, 1, 0.2] }}
        transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
      />
      <ChevronRight className="absolute left-1/2 top-1/2 hidden h-4 w-4 -translate-x-1/2 -translate-y-1/2 rotate-90 text-accent/70 lg:block lg:rotate-0" />
    </div>
  );
}
