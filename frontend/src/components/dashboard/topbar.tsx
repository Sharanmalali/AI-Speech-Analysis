"use client";

import { LogOut, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";

import { Avatar, AvatarFallback } from "@/components/dashboard/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/dashboard/dropdown-menu";
import { ThemeToggle } from "@/components/brand/theme-toggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

function pageTitle(pathname: string): string {
  if (pathname === "/dashboard") return "Overview";
  if (pathname.startsWith("/dashboard/upload")) return "New Analysis";
  if (pathname.startsWith("/dashboard/processing")) return "Processing";
  if (pathname.startsWith("/dashboard/results")) return "Analysis Results";
  if (pathname.startsWith("/dashboard/admin")) return "Administration";
  return "Dashboard";
}

export function DashboardTopbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const initials =
    user?.full_name
      ?.split(" ")
      .map((p) => p[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || user?.email?.[0]?.toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/60 bg-background/70 px-4 backdrop-blur-xl md:px-8">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">AblePro</span>
        <span className="text-muted-foreground/50">/</span>
        <span className="font-display font-semibold">{pageTitle(pathname)}</span>
      </div>

      <div className="flex items-center gap-1.5">
        <div className="mr-1 hidden items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary sm:flex">
          <Sparkles className="h-3.5 w-3.5" />
          AI Enabled
        </div>
        <ThemeToggle />
        <div className="mx-1 hidden h-6 w-px bg-border sm:block" />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 px-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
              <div className="hidden text-left leading-tight sm:block">
                <p className="text-sm font-medium">{user?.full_name || "Account"}</p>
                <p className="text-[11px] capitalize text-muted-foreground">{user?.role}</p>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="font-medium">{user?.full_name || "Account"}</div>
              <div className="text-xs font-normal text-muted-foreground">{user?.email}</div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
