"use client";

import { useMemo } from "react";

import { Card, CardContent } from "@/components/ui/card";
import type { SpeakerRead } from "@/lib/types";
import { formatTimestamp } from "@/lib/utils";

interface Segment {
  start: number;
  end: number;
  label: string;
  color: string;
  source: string | null;
  translated: string | null;
}

export function Transcript({ speakers }: { speakers: SpeakerRead[] }) {
  const segments = useMemo<Segment[]>(() => {
    const all: Segment[] = [];
    for (const s of speakers) {
      for (const t of s.transcriptions) {
        all.push({
          start: t.start_time,
          end: t.end_time,
          label: s.label,
          color: s.color || "#6366F1",
          source: t.text_source,
          translated: t.text_translated,
        });
      }
    }
    return all.sort((a, b) => a.start - b.start);
  }, [speakers]);

  if (segments.length === 0) {
    return (
      <Card className="panel">
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No transcribed speech available.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="panel">
      <CardContent className="max-h-[560px] space-y-4 overflow-y-auto p-5">
        {segments.map((seg, i) => (
          <div key={i} className="border-l-2 pl-4" style={{ borderColor: seg.color }}>
            <div className="mb-1 flex items-center gap-2 text-xs">
              <span className="font-mono text-muted-foreground">
                [{formatTimestamp(seg.start)} - {formatTimestamp(seg.end)}]
              </span>
              <span className="font-semibold" style={{ color: seg.color }}>
                Speaker {seg.label}
              </span>
            </div>
            {seg.translated && <p className="text-sm">{seg.translated}</p>}
            {seg.source && <p className="text-xs text-muted-foreground">{seg.source}</p>}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
