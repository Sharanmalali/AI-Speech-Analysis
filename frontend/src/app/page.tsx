"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Brain,
  FileText,
  Languages,
  Lock,
  Mic2,
  ShieldCheck,
  Sparkles,
  Users,
  Waves,
} from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";

import { AnimatedCounter } from "@/components/motion/counter";
import { Reveal, Stagger, StaggerItem } from "@/components/motion/reveal";
import { AnimatedBackground } from "@/components/marketing/animated-background";
import { MarketingFooter } from "@/components/marketing/footer";
import { MarketingNavbar } from "@/components/marketing/navbar";
import { Button } from "@/components/ui/button";

const HeroScene = dynamic(() => import("@/components/marketing/hero-scene"), { ssr: false });

const METRICS = [
  { value: 6, suffix: "+", label: "AI models orchestrated" },
  { value: 99.9, decimals: 1, suffix: "%", label: "Pipeline uptime target" },
  { value: 2, label: "Languages (KN → EN)" },
  { value: 8, label: "Speakers per session" },
];

const FEATURES = [
  {
    icon: Users,
    title: "Speaker diarization",
    desc: "Pinpoints who spoke when across overlapping, multi-party conversations.",
    span: "md:col-span-2",
    accent: "from-indigo-500/20 to-violet-500/20 text-indigo-500",
  },
  {
    icon: Languages,
    title: "Kannada → English",
    desc: "Transcribes Kannada speech and translates to English with precise timestamps.",
    span: "",
    accent: "from-sky-500/20 to-cyan-500/20 text-sky-500",
  },
  {
    icon: Brain,
    title: "Typical / Atypical",
    desc: "Acoustic-prosodic screening flags atypical speech for clinical review.",
    span: "",
    accent: "from-violet-500/20 to-fuchsia-500/20 text-violet-500",
  },
  {
    icon: Mic2,
    title: "Gender & age",
    desc: "Per-speaker estimation, with an automatic Gemini audio fallback.",
    span: "",
    accent: "from-rose-500/20 to-pink-500/20 text-rose-500",
  },
  {
    icon: FileText,
    title: "Clinical PDF reports",
    desc: "Professionally formatted, downloadable analysis with charts and transcripts.",
    span: "md:col-span-2",
    accent: "from-emerald-500/20 to-teal-500/20 text-emerald-500",
  },
];

const WORKFLOW = [
  { icon: Waves, title: "Upload & clean", desc: "Drag in audio. We reduce noise and standardise the signal." },
  { icon: Users, title: "Diarize & transcribe", desc: "Separate speakers, then transcribe and translate each turn." },
  { icon: Brain, title: "Analyse", desc: "Extract acoustic features and run gender, age and atypicality models." },
  { icon: BarChart3, title: "Report", desc: "Explore an interactive dashboard and export a polished PDF." },
];

const SECURITY = [
  "JWT & refresh tokens",
  "Role-based access",
  "Rate limiting",
  "Strict file validation",
  "Audit trails",
  "Encrypted storage",
  "HTTPS ready",
  "Dockerised deploys",
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <MarketingNavbar />

      {/* HERO */}
      <section className="relative pb-24 pt-32 md:pt-44">
        <AnimatedBackground />
        <div className="absolute inset-0 -z-10 bg-grid opacity-[0.5]" />

        <div className="container grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/60 px-3.5 py-1.5 text-xs font-medium shadow-soft backdrop-blur"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
              </span>
              AI-Powered Mental Health Audio Analytics
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.05 }}
              className="font-display text-[2.75rem] font-extrabold leading-[1.05] tracking-tight text-balance md:text-6xl lg:text-[4.25rem]"
            >
              Understand every <span className="gradient-text animate-gradient-pan">voice</span> in
              the conversation.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.12 }}
              className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground"
            >
              AblePro analyses multi-speaker recordings end to end — diarization,
              Kannada-to-English transcription, gender &amp; age estimation, and
              typical/atypical screening — in one beautiful dashboard.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.18 }}
              className="mt-9 flex flex-wrap items-center gap-3"
            >
              <Button asChild variant="gradient" size="lg">
                <Link href="/register">
                  Start analysing <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/login">Sign in</Link>
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-12 grid max-w-lg grid-cols-2 gap-x-8 gap-y-6 sm:grid-cols-4"
            >
              {METRICS.map((m) => (
                <div key={m.label}>
                  <div className="font-display text-2xl font-bold tracking-tight">
                    <AnimatedCounter value={m.value} decimals={m.decimals} suffix={m.suffix} />
                  </div>
                  <p className="mt-1 text-xs leading-tight text-muted-foreground">{m.label}</p>
                </div>
              ))}
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="glass-strong relative h-[360px] overflow-hidden rounded-[2rem] shadow-elevated md:h-[480px]">
              <HeroScene />
              <div className="pointer-events-none absolute bottom-4 left-4 right-4 flex items-center gap-3 rounded-2xl border border-white/20 bg-background/60 p-3 backdrop-blur-xl">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-white">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="text-sm">
                  <p className="font-semibold leading-tight">Live analysis engine</p>
                  <p className="text-xs text-muted-foreground">Diarization · ASR · screening</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FEATURES (BENTO) */}
      <section id="features" className="container py-20 md:py-28">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <p className="eyebrow justify-center">
            <Sparkles className="h-3.5 w-3.5" /> Capabilities
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight md:text-[2.6rem]">
            Everything you need, in one pipeline
          </h2>
          <p className="mt-3 text-muted-foreground">
            A service-oriented ML backend keeps each model independent, fast and reliable.
          </p>
        </Reveal>

        <Stagger className="grid gap-5 md:grid-cols-3">
          {FEATURES.map((f) => (
            <StaggerItem key={f.title} className={f.span}>
              <motion.div
                whileHover={{ y: -6 }}
                transition={{ type: "spring", stiffness: 300, damping: 22 }}
                className="panel group h-full overflow-hidden p-7"
              >
                <div className={`mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${f.accent}`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </motion.div>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      {/* WORKFLOW */}
      <section id="workflow" className="container py-20 md:py-28">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <p className="eyebrow justify-center">
            <Waves className="h-3.5 w-3.5" /> How it works
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight md:text-[2.6rem]">
            From raw audio to clinical insight
          </h2>
        </Reveal>

        <Stagger className="grid gap-5 md:grid-cols-4">
          {WORKFLOW.map((step, i) => (
            <StaggerItem key={step.title}>
              <div className="panel relative h-full p-6">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <step.icon className="h-5 w-5" />
                  </div>
                  <span className="font-display text-3xl font-extrabold text-muted-foreground/20">
                    0{i + 1}
                  </span>
                </div>
                <h3 className="font-semibold">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{step.desc}</p>
              </div>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      {/* SECURITY */}
      <section id="security" className="container py-20 md:py-28">
        <Reveal>
          <div className="panel relative overflow-hidden p-8 md:p-12">
            <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
            <div className="relative grid items-center gap-10 md:grid-cols-2">
              <div>
                <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h2 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
                  Secure &amp; production-ready
                </h2>
                <p className="mt-4 max-w-md leading-relaxed text-muted-foreground">
                  Enterprise-grade security is built in from day one, not bolted on — so sensitive
                  clinical audio stays protected at every step.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {SECURITY.map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2.5 rounded-2xl border border-border/60 bg-secondary/40 px-4 py-3 text-sm font-medium"
                  >
                    <Lock className="h-4 w-4 shrink-0 text-primary" />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* CTA */}
      <section className="container pb-24 pt-4">
        <Reveal>
          <div className="relative overflow-hidden rounded-[2rem] border border-primary/20 bg-gradient-to-br from-primary to-accent p-10 text-center text-white shadow-glow md:p-16">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.25),transparent_50%)]" />
            <div className="relative">
              <h2 className="mx-auto max-w-2xl font-display text-3xl font-bold tracking-tight md:text-5xl">
                Ready to hear what your audio is really saying?
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-white/85">
                Create an account and run your first multi-speaker analysis in minutes.
              </p>
              <div className="mt-8 flex justify-center">
                <Button asChild size="xl" className="bg-white text-primary hover:bg-white/90">
                  <Link href="/register">
                    Get started free <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <MarketingFooter />
    </div>
  );
}
