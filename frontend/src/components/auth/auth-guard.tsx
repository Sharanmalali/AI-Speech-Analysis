"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuthStore } from "@/lib/store/auth-store";

/** Client-side guard: redirects unauthenticated users to /login. */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, accessToken, hydrated } = useAuthStore();

  useEffect(() => {
    if (hydrated && (!accessToken || !user)) {
      router.replace("/login");
    }
  }, [hydrated, accessToken, user, router]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!accessToken || !user) return null;

  return <>{children}</>;
}
