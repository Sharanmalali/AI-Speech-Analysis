"use client";

import { motion } from "framer-motion";
import { MessagesSquare } from "lucide-react";
import { useMemo, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import type { SpeakerRead } from "@/lib/types";
import { cn, formatTimestamp } from "@/lib/utils";

const FALLBACK = "#6366F1";

interface Message {
  id: string;
  start: number;
  end: number;
  label: string;
  color: string;
  source: string | null;
  translated: string | null;
}

/** Append an alpha channel to a #RRGGBB hex string. */
function withAlpha(hex: string, alpha: string): string {
  return /^#[0-9a-fA-F]{6}$/.test(hex) ? `${hex}${alpha}` : hex;
}

export function Transcript({ speakers }: { speakers: SpeakerRead[] }) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  const messages = useMemo<Message[]>(() => {
    const all: Message[] = [];
    for (const s of speakers) {
      for (const t of s.transcriptions) {
        all.push({
          id: t.id,
          start: t.start_time,
          end: t.end_time,
          label: s.label,
          color: s.color || FALLBACK,
          source: t.text_source,
          translated: t.text_translated,
        });
      }
    }
    return all.sort((a, b) => a.start - b.start);
  }, [speakers]);

  const visible = messages.filter((m) => !hidden.has(m.label));

  function toggle(label: string) {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  if (messages.length === 0) {
    return (
      <Card className="panel">
        <CardContent className="flex flex-col items-center gap-2 py-12 text-center text-sm text-muted-foreground">
          <MessagesSquare className="h-7 w-7 opacity-50" />
          No transcribed speech available.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="panel overflow-hidden">
      {/* Speaker filter bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border/60 bg-secondary/30 px-5 py-3.5">
        <span className="mr-1 inline-flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
          <MessagesSquare className="h-3.5 w-3.5" /> Conversation
        </span>
        {speakers.map((s) => {
          const color = s.color || FALLBACK;
          const off = hidden.has(s.label);
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => toggle(s.label)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium transition-all",
                off
                  ? "border-border/60 bg-transparent text-muted-foreground/60 opacity-60"
                  : "border-transparent text-foreground",
              )}
              style={off ? undefined : { background: withAlpha(color, "1A") }}
            >
              <span
                className="flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold text-white"
                style={{ background: color }}
              >
                {s.label}
              </span>
              Speaker {s.label}
              <span className="text-[10px] text-muted-foreground">{s.transcriptions.length}</span>
            </button>
          );
        })}
      </div>

      <CardContent className="max-h-[560px] space-y-3 overflow-y-auto p-5">
        {visible.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            All speakers hidden — tap a speaker above to show their messages.
          </p>
        ) : (
          visible.map((m, i) => {
            const prev = visible[i - 1];
            const grouped = prev && prev.label === m.label;
            return (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(i * 0.015, 0.3) }}
                className={cn("flex items-start gap-3", grouped ? "mt-1" : "mt-3 first:mt-0")}
              >
                {/* Avatar (hidden when grouped with previous message) */}
                <div className="w-9 shrink-0">
                  {!grouped && (
                    <div
                      className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white shadow-sm"
                      style={{ background: m.color }}
                    >
                      {m.label}
                    </div>
                  )}
                </div>

                {/* Bubble */}
                <div className="min-w-0 flex-1">
                  {!grouped && (
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{ color: m.color }}>
                        Speaker {m.label}
                      </span>
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {formatTimestamp(m.start)} – {formatTimestamp(m.end)}
                      </span>
                    </div>
                  )}
                  <div
                    className="rounded-2xl rounded-tl-sm border px-4 py-2.5"
                    style={{
                      background: withAlpha(m.color, "12"),
                      borderColor: withAlpha(m.color, "33"),
                    }}
                  >
                    {m.translated && (
                      <p className="text-sm leading-relaxed text-foreground">{m.translated}</p>
                    )}
                    {m.source && (
                      <p className="mt-1.5 flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
                        <span className="mt-px rounded bg-muted px-1 py-px text-[9px] font-bold uppercase tracking-wide">
                          KN
                        </span>
                        <span className="min-w-0">{m.source}</span>
                      </p>
                    )}
                    {grouped && (
                      <span className="mt-1 block font-mono text-[10px] text-muted-foreground/70">
                        {formatTimestamp(m.start)}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
