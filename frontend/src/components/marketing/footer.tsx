import Link from "next/link";

import { Logo } from "@/components/brand/logo";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Workflow", href: "#workflow" },
      { label: "Security", href: "#security" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Sign in", href: "/login" },
      { label: "Get started", href: "/register" },
    ],
  },
];

export function MarketingFooter() {
  return (
    <footer className="relative mt-10 border-t border-border/60">
      <div className="container py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr]">
          <div className="max-w-sm space-y-4">
            <Logo />
            <p className="text-sm leading-relaxed text-muted-foreground">
              AI-powered multi-speaker mental health audio analytics — diarization,
              transcription, and clinical-grade speech screening in one platform.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="mb-3 text-sm font-semibold">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border/60 pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} AblePro Solutions. All rights reserved.</p>
          <p>AI-Powered Mental Health Audio Analytics Platform</p>
        </div>
      </div>
    </footer>
  );
}
