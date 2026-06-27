"use client";

import { motion } from "framer-motion";
import { AudioLines, LayoutDashboard, ShieldCheck, Sparkles, Upload } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/upload", label: "New Analysis", icon: Upload, exact: false },
];

const ADMIN_NAV = [
  { href: "/dashboard/admin", label: "Administration", icon: ShieldCheck, exact: false },
];

export function DashboardSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user?.role === "admin" ? [...NAV, ...ADMIN_NAV] : NAV;

  return (
    <aside className="sticky top-0 hidden h-screen w-[264px] shrink-0 flex-col border-r border-border/60 bg-card/30 backdrop-blur-xl lg:flex">
      <div className="flex h-16 items-center gap-2.5 border-b border-border/60 px-5">
        <Link href="/dashboard" aria-label="AblePro home" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-soft">
            <AudioLines className="h-5 w-5 text-white" />
          </div>
          <div className="leading-tight">
            <span className="block font-display text-[15px] font-bold tracking-tight">AblePro</span>
            <span className="block text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Solutions
            </span>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5">
        <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Workspace
        </p>
        {items.map((item) => {
          const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                active ? "text-primary" : "text-muted-foreground hover:bg-secondary hover:text-foreground",
              )}
            >
              {active && (
                <motion.span
                  layoutId="sidebar-active"
                  className="absolute inset-0 -z-10 rounded-xl bg-primary/10"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <item.icon className="h-[18px] w-[18px]" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3">
        <div className="relative overflow-hidden rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/10 to-accent/10 p-4">
          <div className="mb-1 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">AI Analytics</span>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Diarization, transcription &amp; clinical speech screening.
          </p>
        </div>
        <p className="mt-3 px-1 text-center text-[11px] capitalize text-muted-foreground">
          {user?.role ?? "user"} workspace
        </p>
      </div>
    </aside>
  );
}
