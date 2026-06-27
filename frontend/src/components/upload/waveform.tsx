"use client";

import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/lib/utils";

/** Renders an interactive waveform for a local File or remote URL via wavesurfer.js. */
export function Waveform({ file, url }: { file?: File; url?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<import("wavesurfer.js").default | null>(null);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    let destroyed = false;
    let objectUrl: string | undefined;

    (async () => {
      const WaveSurfer = (await import("wavesurfer.js")).default;
      if (destroyed || !containerRef.current) return;

      const ws = WaveSurfer.create({
        container: containerRef.current,
        waveColor: "#a5b4fc",
        progressColor: "#6366f1",
        cursorColor: "#ec4899",
        barWidth: 2,
        barGap: 2,
        barRadius: 3,
        height: 80,
      });
      wsRef.current = ws;

      const src = file ? (objectUrl = URL.createObjectURL(file)) : url;
      if (src) await ws.load(src);

      ws.on("ready", () => setDuration(ws.getDuration()));
      ws.on("audioprocess", () => setCurrent(ws.getCurrentTime()));
      ws.on("interaction", () => setCurrent(ws.getCurrentTime()));
      ws.on("play", () => setPlaying(true));
      ws.on("pause", () => setPlaying(false));
      ws.on("finish", () => setPlaying(false));
    })();

    return () => {
      destroyed = true;
      wsRef.current?.destroy();
      wsRef.current = null;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [file, url]);

  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-4">
        <Button
          type="button"
          size="icon"
          variant="gradient"
          onClick={() => wsRef.current?.playPause()}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
        <div ref={containerRef} className="min-w-0 flex-1" />
      </div>
      <div className="mt-2 flex justify-between text-xs text-muted-foreground">
        <span>{formatTimestamp(current)}</span>
        <span>{formatTimestamp(duration)}</span>
      </div>
    </div>
  );
}
