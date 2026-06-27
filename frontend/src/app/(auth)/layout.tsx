import { AudioLines, CheckCircle2 } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/brand/theme-toggle";

const HIGHLIGHTS = [
  "Multi-speaker diarization & transcription",
  "Gender, age & atypicality screening",
  "Clinical-grade PDF reports in one click",
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-primary via-primary to-accent p-12 text-white lg:flex">
        <div className="absolute inset-0 aurora opacity-40 mix-blend-overlay" />
        <div className="absolute -bottom-24 -left-16 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -right-16 top-10 h-72 w-72 rounded-full bg-white/10 blur-3xl" />

        <Link href="/" className="relative flex items-center gap-2.5 text-white">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <AudioLines className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <span className="block text-base font-bold">AblePro</span>
            <span className="block text-[10px] font-medium uppercase tracking-widest text-white/70">
              Solutions
            </span>
          </div>
        </Link>

        <div className="relative max-w-md">
          <h2 className="font-display text-4xl font-bold leading-tight tracking-tight">
            Hear what your audio is really saying.
          </h2>
          <p className="mt-4 text-white/80">
            The AI platform for multi-speaker mental-health audio analytics.
          </p>
          <ul className="mt-8 space-y-3">
            {HIGHLIGHTS.map((h) => (
              <li key={h} className="flex items-center gap-3 text-sm text-white/90">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-white/80" />
                {h}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-white/60">
          © {new Date().getFullYear()} AblePro Solutions
        </p>
      </div>

      {/* Form panel */}
      <div className="relative flex flex-col">
        <div className="flex items-center justify-between p-5 lg:justify-end">
          <Link href="/" className="lg:hidden">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
        <div className="flex flex-1 items-center justify-center px-5 pb-16">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </div>
    </div>
  );
}
