"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, AudioLines, Clock, Download, Gauge, Loader2, Sparkles, Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { ThemeToggle } from "@/components/brand/theme-toggle";
import { StatCard } from "@/components/dashboard/stat-card";
import { AnimatedCounter } from "@/components/motion/counter";
import { SpeakingTimeChart, SpeechPauseChart } from "@/components/results/charts";
import { SpeakerCard } from "@/components/results/speaker-card";
import { Timeline } from "@/components/results/timeline";
import { Transcript } from "@/components/results/transcript";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getErrorMessage } from "@/lib/api";
import { demoService } from "@/lib/services";
import { formatTimestamp } from "@/lib/utils";

export default function DemoPage() {
  const [downloading] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["demo-result"],
    queryFn: () => demoService.getSampleResult(),
    retry: false,
    staleTime: Infinity, // Demo data never goes stale
  });

  function handleDownloadClick() {
    toast.info("Demo PDF download is not available in demo mode", {
      description: "Sign up to upload your own audio and download real reports",
    });
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-muted/30">
        {/* Simple Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl md:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-soft">
              <AudioLines className="h-5 w-5 text-white" />
            </div>
            <span className="font-display text-lg font-bold">AblePro Demo</span>
          </div>
          <ThemeToggle />
        </header>

        <main className="relative">
          <div className="pointer-events-none absolute inset-0 bg-dots opacity-50" />
          <div className="relative mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
            <div className="space-y-6">
              <Skeleton className="h-20 rounded-3xl" />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-[88px] rounded-3xl" />
                ))}
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <Skeleton className="h-64 rounded-3xl" />
                <Skeleton className="h-64 rounded-3xl" />
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-muted/30">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl md:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-soft">
              <AudioLines className="h-5 w-5 text-white" />
            </div>
            <span className="font-display text-lg font-bold">AblePro Demo</span>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/">
              <ArrowLeft className="h-4 w-4" /> Back to Home
            </Link>
          </Button>
        </header>
        <main className="relative">
          <div className="mx-auto max-w-7xl px-4 py-16">
            <div className="panel flex flex-col items-center gap-3 py-16 text-center">
              <AlertTriangle className="h-8 w-8 text-destructive" />
              <p className="text-muted-foreground">{getErrorMessage(error)}</p>
              <Button asChild className="mt-4">
                <Link href="/">Back to Home</Link>
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const duration = data.audio.duration_seconds || 0;
  const atypicalCount = data.speakers.filter((s) => s.prediction?.atypicality === "atypical").length;

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Public Header - No Auth Required */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl md:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-soft">
            <AudioLines className="h-5 w-5 text-white" />
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="font-display font-bold">AblePro</span>
            <span className="text-muted-foreground/50">/</span>
            <span className="font-semibold text-muted-foreground">Demo Analysis</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary sm:flex">
            <Sparkles className="h-3.5 w-3.5" />
            Demo Mode
          </div>
          <ThemeToggle />
          <Button asChild variant="outline" size="sm">
            <Link href="/">
              <ArrowLeft className="h-4 w-4" /> Back to Home
            </Link>
          </Button>
        </div>
      </header>

      <main className="relative">
        <div className="pointer-events-none absolute inset-0 bg-dots opacity-50" />
        <div className="relative mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
          <div className="space-y-8">
            {/* Demo Banner */}
            <div className="relative overflow-hidden rounded-2xl border-2 border-primary/30 bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-white">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">Demo Mode - Public Access</h3>
                  <p className="text-sm text-muted-foreground">
                    This is a sample analysis showcasing AblePro's capabilities. Sign up to analyze your own audio files!
                  </p>
                </div>
              </div>
            </div>

            {/* Page Header */}
            <div className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Sample Analysis Results</p>
                  <h1 className="mt-1 font-display text-3xl font-bold tracking-tight md:text-4xl">
                    {data.audio.original_filename}
                  </h1>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {data.language_source.toUpperCase()} → {data.language_target.toUpperCase()} · transcribed & screened
                  </p>
                </div>
                <Button variant="gradient" onClick={handleDownloadClick} disabled={downloading}>
                  {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                  Download PDF
                </Button>
              </div>
            </div>

            {/* KPI row */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Speakers" value={<AnimatedCounter value={data.detected_speakers} />} icon={Users} accent="primary" />
              <StatCard label="Duration" value={formatTimestamp(duration)} icon={Clock} accent="sky" />
              <StatCard
                label="Atypical speakers"
                value={<AnimatedCounter value={atypicalCount} />}
                icon={AlertTriangle}
                accent={atypicalCount > 0 ? "rose" : "emerald"}
              />
              <StatCard
                label="Processing time"
                value={`${(data.processing_time_seconds ?? 0).toFixed(1)}s`}
                icon={Gauge}
                accent="amber"
              />
            </div>

            <Tabs defaultValue="overview" className="space-y-2">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="speakers">Speakers</TabsTrigger>
                <TabsTrigger value="transcript">Transcript</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <SpeakingTimeChart speakers={data.speakers} />
                  <SpeechPauseChart speakers={data.speakers} />
                </div>
                <Timeline speakers={data.speakers} duration={duration} />
              </TabsContent>

              <TabsContent value="speakers">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {data.speakers.map((s, i) => (
                    <SpeakerCard key={s.id} speaker={s} index={i} />
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="transcript">
                <Transcript speakers={data.speakers} />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  );
}
