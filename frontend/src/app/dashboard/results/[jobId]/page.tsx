"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Clock, Download, Gauge, Loader2, Users } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
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
import { reportService, resultService } from "@/lib/services";
import { formatTimestamp } from "@/lib/utils";

export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [downloading, setDownloading] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["results", jobId],
    queryFn: () => resultService.get(jobId),
    retry: false,
  });

  async function downloadReport() {
    setDownloading(true);
    try {
      const blob = await reportService.download(jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ablepro_report_${jobId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Report downloaded");
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDownloading(false);
    }
  }

  if (isLoading) {
    return (
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
    );
  }

  if (isError || !data) {
    return (
      <div className="panel flex flex-col items-center gap-3 py-16 text-center">
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <p className="text-muted-foreground">{getErrorMessage(error)}</p>
      </div>
    );
  }

  const duration = data.audio.duration_seconds || 0;
  const atypicalCount = data.speakers.filter((s) => s.prediction?.atypicality === "atypical").length;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Analysis results"
        title={data.audio.original_filename}
        description={`${data.language_source.toUpperCase()} → ${data.language_target.toUpperCase()} · transcribed & screened`}
        actions={
          <Button variant="gradient" onClick={downloadReport} disabled={downloading}>
            {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            Download PDF
          </Button>
        }
      />

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
  );
}
