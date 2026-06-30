import Link from "next/link";
import { ArrowLeft, AudioLines, Sparkles } from "lucide-react";

import { ThemeToggle } from "@/components/brand/theme-toggle";
import { Button } from "@/components/ui/button";

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-muted/30">
      {/* Simple topbar for demo */}
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

      <main className="relative flex-1">
        <div className="pointer-events-none absolute inset-0 bg-dots opacity-50" />
        <div className="relative mx-auto w-full max-w-7xl px-4 py-8 md:px-8">{children}</div>
      </main>
    </div>
  );
}
