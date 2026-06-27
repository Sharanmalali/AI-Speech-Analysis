"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Brain,
  FileCheck2,
  FileText,
  Gauge,
  KeyRound,
  Languages,
  Lock,
  Mic2,
  ScrollText,
  Server,
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
import { Workflow3D } from "@/components/marketing/workflow-3d";
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
    accent: "from-indigo-500/20 to-violet-500/20 text-indigo-500",
  },
  {
    icon: Languages,
    title: "Kannada → English",
    desc: "Transcribes Kannada speech and translates to English with precise timestamps.",
    accent: "from-sky-500/20 to-cyan-500/20 text-sky-500",
  },
  {
    icon: Brain,
    title: "Typical / Atypical",
    desc: "Acoustic-prosodic screening flags atypical speech for clinical review.",
    accent: "from-violet-500/20 to-fuchsia-500/20 text-violet-500",
  },
  {
    icon: Mic2,
    title: "Gender & age",
    desc: "Per-speaker estimation via dedicated wav2vec2 models, with an AI fallback.",
    accent: "from-rose-500/20 to-pink-500/20 text-rose-500",
  },
  {
    icon: BarChart3,
    title: "Interactive dashboard",
    desc: "Timelines, charts and a group-chat transcript make every result explorable.",
    accent: "from-amber-500/20 to-orange-500/20 text-amber-500",
  },
  {
    icon: FileText,
    title: "Clinical PDF reports",
    desc: "Professionally formatted, downloadable analysis with charts and transcripts.",
    accent: "from-emerald-500/20 to-teal-500/20 text-emerald-500",
  },
];

const SECURITY = [
  {
    icon: KeyRound,
    title: "JWT + refresh tokens",
    desc: "Short-lived access tokens with secure, rotating refresh sessions.",
  },
  {
    icon: ShieldCheck,
    title: "Role-based access",
    desc: "Admin, doctor and user roles guard every protected endpoint.",
  },
  {
    icon: Gauge,
    title: "Rate limiting & throttling",
    desc: "Redis-backed limits shield auth and upload routes from abuse.",
  },
  {
    icon: FileCheck2,
    title: "Strict file validation",
    desc: "Content-type, extension and size checks on every upload.",
  },
  {
    icon: ScrollText,
    title: "Audit trails",
    desc: "Every sensitive action is logged for full accountability.",
  },
  {
    icon: Lock,
    title: "Encrypted storage",
    desc: "Audio and reports are stored privately with signed access.",
  },
  {
    icon: Server,
    title: "HTTPS ready",
    desc: "TLS-terminating NGINX proxy and secure cookie defaults.",
  },
  {
    icon: Sparkles,
    title: "Hardened by default",
    desc: "Input validation, CORS and no secrets in source — built in.",
  },
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

        <Stagger className="grid items-stretch gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <StaggerItem key={f.title} className="h-full">
              <motion.div
                whileHover={{ y: -6 }}
                transition={{ type: "spring", stiffness: 300, damping: 22 }}
                className="panel sheen group flex h-full flex-col p-7"
              >
                <div className={`mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${f.accent} transition-transform duration-300 group-hover:scale-110`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-display text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </motion.div>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      {/* WORKFLOW — interactive 3D pipeline */}
      <section id="workflow" className="container py-20 md:py-28">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <p className="eyebrow justify-center">
            <Waves className="h-3.5 w-3.5" /> How it works
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight md:text-[2.6rem]">
            From raw audio to clinical insight
          </h2>
          <p className="mt-3 text-muted-foreground">
            Each upload flows through an orchestrated pipeline of independent AI services —
            explore the full journey in 3D.
          </p>
        </Reveal>

        <Workflow3D />
      </section>

      {/* SECURITY */}
      <section id="security" className="container py-20 md:py-28">
        <Reveal className="mx-auto mb-12 max-w-2xl text-center">
          <p className="eyebrow justify-center">
            <ShieldCheck className="h-3.5 w-3.5" /> Security &amp; trust
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight md:text-[2.6rem]">
            Enterprise-grade by design
          </h2>
          <p className="mt-3 text-muted-foreground">
            Sensitive clinical audio deserves more than an afterthought. Security is built into
            every layer of the stack — from the token to the container.
          </p>
        </Reveal>

        <Stagger className="grid items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SECURITY.map((s) => (
            <StaggerItem key={s.title} className="h-full">
              <motion.div
                whileHover={{ y: -5 }}
                transition={{ type: "spring", stiffness: 300, damping: 22 }}
                className="panel group relative flex h-full flex-col overflow-hidden p-6"
              >
                <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full bg-emerald-500/10 blur-2xl transition-opacity duration-300 group-hover:opacity-100 md:opacity-0" />
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 text-emerald-600 transition-transform duration-300 group-hover:scale-110 dark:text-emerald-400">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="font-display text-base font-semibold leading-tight">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.desc}</p>
              </motion.div>
            </StaggerItem>
          ))}
        </Stagger>

        <Reveal className="mt-6">
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 rounded-2xl border border-border/60 bg-secondary/30 px-6 py-4 text-sm">
            {[
              "OWASP-aligned",
              "100% inputs validated",
              "Dockerised deploys",
              "No secrets in source",
            ].map((t) => (
              <span key={t} className="inline-flex items-center gap-2 font-medium text-muted-foreground">
                <ShieldCheck className="h-4 w-4 text-emerald-500" /> {t}
              </span>
            ))}
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
