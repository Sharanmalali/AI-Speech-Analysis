"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

/** Premium aurora backdrop: soft drifting gradient orbs + faint particles. */
export function AnimatedBackground({ particles: showParticles = true }: { particles?: boolean }) {
  const particles = useMemo(
    () =>
      Array.from({ length: 18 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        top: Math.random() * 100,
        size: 1.5 + Math.random() * 3,
        duration: 10 + Math.random() * 12,
        delay: Math.random() * 6,
      })),
    [],
  );

  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 aurora opacity-90" />

      <motion.div
        className="absolute -left-32 top-0 h-96 w-96 rounded-full bg-primary/25 blur-[120px]"
        animate={{ x: [0, 40, 0], y: [0, 30, 0] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute right-0 top-1/4 h-96 w-96 rounded-full bg-accent/20 blur-[120px]"
        animate={{ x: [0, -30, 0], y: [0, 40, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 2 }}
      />

      {showParticles &&
        particles.map((p) => (
          <motion.span
            key={p.id}
            className="absolute rounded-full bg-foreground/25"
            style={{ left: `${p.left}%`, top: `${p.top}%`, width: p.size, height: p.size }}
            animate={{ y: [0, -36, 0], opacity: [0.08, 0.5, 0.08] }}
            transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
          />
        ))}
    </div>
  );
}
