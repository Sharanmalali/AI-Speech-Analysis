"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { toast } from "sonner";

import { getErrorMessage } from "@/lib/api";
import { authService } from "@/lib/services";
import { useAuthStore } from "@/lib/store/auth-store";

export function useAuth() {
  const router = useRouter();
  const { user, accessToken, hydrated, setAuth, clear } = useAuthStore();

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authService.login(email, password);
      setAuth(res.user, res.tokens.access_token);
      return res.user;
    },
    [setAuth],
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const res = await authService.register(email, password, fullName);
      setAuth(res.user, res.tokens.access_token);
      return res.user;
    },
    [setAuth],
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      // Non-fatal: clear the local session regardless.
      console.warn(getErrorMessage(error));
    }
    clear();
    toast.success("Signed out");
    router.push("/login");
  }, [clear, router]);

  return {
    user,
    isAuthenticated: Boolean(accessToken && user),
    hydrated,
    login,
    register,
    logout,
  };
}
