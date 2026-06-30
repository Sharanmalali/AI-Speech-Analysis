"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SpeakerRead } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

export function Timeline({
  speakers,
  duration,
}: {
  speakers: SpeakerRead[];
  duration: number;
}) {
  const total = duration || 1;

  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle className="text-base">Conversation timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {speakers.map((s) => {
          const speakerNum = s.label.replace(/[^0-9]/g, "");
          return (
            <div key={s.id} className="flex items-center gap-3">
              <div className="w-16 shrink-0 text-sm font-medium" style={{ color: s.color || undefined }}>
                Spk {speakerNum}
              </div>
              <div className="relative h-7 flex-1 overflow-hidden rounded-lg bg-muted/50">
                {s.transcriptions.map((t) => {
                  const left = (t.start_time / total) * 100;
                  const width = Math.max(0.5, ((t.end_time - t.start_time) / total) * 100);
                  return (
                    <div
                      key={t.id}
                      className="absolute top-0 h-full rounded-md opacity-90"
                      style={{ left: `${left}%`, width: `${width}%`, background: s.color || "#6366F1" }}
                      title={`${formatTimestamp(t.start_time)} - ${formatTimestamp(t.end_time)}`}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
        <div className="flex justify-between pl-[76px] text-xs text-muted-foreground">
          <span>0:00</span>
          <span>{formatTimestamp(total)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
