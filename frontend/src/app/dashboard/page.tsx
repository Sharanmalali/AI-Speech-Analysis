"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, CheckCircle2, FileAudio, Plus, Trash2, Upload, Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { JobStatusBadge } from "@/components/dashboard/job-status-badge";
import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { AnimatedCounter } from "@/components/motion/counter";
import { Stagger, StaggerItem } from "@/components/motion/reveal";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { getErrorMessage } from "@/lib/api";
import { jobService } from "@/lib/services";
import type { JobWithAudio } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

const INITIAL_VISIBLE = 6;

function jobHref(job: JobWithAudio): string {
  if (job.status === "completed" || job.status === "failed" || job.status === "cancelled")
    return `/dashboard/results/${job.id}`;
  return `/dashboard/processing/${job.id}`;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<JobWithAudio | null>(null);
  const [showAll, setShowAll] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", 1],
    queryFn: () => jobService.list(1, 50),
    refetchInterval: 8_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => jobService.remove(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Analysis deleted");
      setTarget(null);
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const items = data?.items ?? [];
  const completed = items.filter((j) => j.status === "completed").length;
  const active = items.filter((j) => ["pending", "queued", "processing"].includes(j.status)).length;
  const speakers = items.reduce((sum, j) => sum + (j.detected_speakers ?? 0), 0);
  const visible = showAll ? items : items.slice(0, INITIAL_VISIBLE);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title={`Welcome${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
        description="Monitor your recent multi-speaker speech analyses."
        actions={
          <Button asChild variant="gradient">
            <Link href="/dashboard/upload">
              <Plus className="h-4 w-4" /> New analysis
            </Link>
          </Button>
        }
      />

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[88px] rounded-3xl" />)
        ) : (
          <>
            <StatCard label="Total analyses" value={<AnimatedCounter value={data?.total ?? 0} />} icon={FileAudio} accent="primary" />
            <StatCard label="Completed" value={<AnimatedCounter value={completed} />} icon={CheckCircle2} accent="emerald" />
            <StatCard label="In progress" value={<AnimatedCounter value={active} />} icon={Activity} accent="amber" />
            <StatCard label="Speakers detected" value={<AnimatedCounter value={speakers} />} icon={Users} accent="sky" />
          </>
        )}
      </div>

      {/* Recent analyses */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold tracking-tight">Recent analyses</h2>
          {items.length > INITIAL_VISIBLE && (
            <Button variant="ghost" size="sm" onClick={() => setShowAll((s) => !s)}>
              {showAll ? "Show less" : `Show all (${items.length})`}
            </Button>
          )}
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-40 rounded-3xl" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="panel relative flex flex-col items-center justify-center gap-4 overflow-hidden py-20 text-center">
            <div className="absolute inset-x-0 top-0 h-40 aurora opacity-30" />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary to-accent text-white shadow-glow">
              <Upload className="h-7 w-7" />
            </div>
            <div className="relative">
              <h3 className="font-display text-xl font-semibold">No analyses yet</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Upload a conversation recording to run your first analysis.
              </p>
            </div>
            <Button asChild variant="gradient" size="lg" className="relative">
              <Link href="/dashboard/upload">
                <Plus className="h-4 w-4" /> Upload audio
              </Link>
            </Button>
          </div>
        ) : (
          <Stagger className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((job) => {
              const inProgress = ["pending", "queued", "processing"].includes(job.status);
              return (
                <StaggerItem key={job.id}>
                  <Link href={jobHref(job)} className="group relative block h-full">
                    {/* Delete button — sits above the link, stops navigation */}
                    <button
                      type="button"
                      aria-label="Delete analysis"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setTarget(job);
                      }}
                      className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground opacity-0 transition-all hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 group-hover:opacity-100"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>

                    <div className="panel panel-hover flex h-full flex-col gap-4 p-5">
                      <div className="flex items-start justify-between gap-2 pr-9">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
                          <FileAudio className="h-5 w-5 text-primary" />
                        </div>
                        <JobStatusBadge status={job.status} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p
                          className="truncate font-semibold transition-colors group-hover:text-primary"
                          title={job.audio_file.original_filename}
                        >
                          {job.audio_file.original_filename}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {formatBytes(job.audio_file.size_bytes)}
                          {job.detected_speakers ? ` · ${job.detected_speakers} speakers` : ""}
                        </p>
                      </div>
                      {inProgress && (
                        <div className="space-y-1.5">
                          <Progress value={job.progress} />
                          <p className="text-right text-[11px] tabular-nums text-muted-foreground">
                            {Math.round(job.progress)}%
                          </p>
                        </div>
                      )}
                      <p className="text-[11px] text-muted-foreground">
                        {new Date(job.created_at).toLocaleString()}
                      </p>
                    </div>
                  </Link>
                </StaggerItem>
              );
            })}
          </Stagger>
        )}
      </div>

      <ConfirmDialog
        open={target !== null}
        title="Delete this analysis?"
        description={
          target
            ? `"${target.audio_file.original_filename}" and its results, transcript and report will be permanently removed. This cannot be undone.`
            : undefined
        }
        confirmLabel="Delete"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => target && deleteMutation.mutate(target.id)}
        onCancel={() => !deleteMutation.isPending && setTarget(null)}
      />
    </div>
  );
}
