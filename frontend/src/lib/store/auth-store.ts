import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { UserProfile } from "@/lib/types";

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  hydrated: boolean;
  setAuth: (user: UserProfile, accessToken: string) => void;
  setAccessToken: (accessToken: string) => void;
  setUser: (user: UserProfile) => void;
  clear: () => void;
  setHydrated: () => void;
}

/**
 * Auth store. The access token is kept here (and persisted to localStorage so
 * a refresh survives a reload). The refresh token lives only in an HttpOnly
 * cookie managed by the backend and is never exposed to JS.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      hydrated: false,
      setAuth: (user, accessToken) => set({ user, accessToken }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      clear: () => set({ user: null, accessToken: null }),
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "ablepro-auth",
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken }),
      onRehydrateStorage: () => (state) => state?.setHydrated(),
    },
  ),
);
