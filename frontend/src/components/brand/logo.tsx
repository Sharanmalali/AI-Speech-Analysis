import { AudioLines } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ className, showText = true }: { className?: string; showText?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/30">
        <AudioLines className="h-5 w-5 text-white" />
      </div>
      {showText && (
        <div className="leading-tight">
          <span className="block text-base font-bold tracking-tight">AblePro</span>
          <span className="block text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            Solutions
          </span>
        </div>
      )}
    </div>
  );
}
