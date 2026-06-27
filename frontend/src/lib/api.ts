import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import { useAuthStore } from "@/lib/store/auth-store";

/**
 * Base URL. In the browser we hit the same origin (Next.js rewrites proxy
 * ``/api`` to the backend). On the server we can target the backend directly.
 */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "";

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  withCredentials: true, // send/receive the refresh cookie
  headers: { "Content-Type": "application/json" },
});

// Attach the access token to every request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Transparent refresh on 401 -------------------------------------------
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await axios.post(
      `${BASE_URL}/api/v1/auth/refresh`,
      {},
      { withCredentials: true },
    );
    const token = res.data?.access_token as string | undefined;
    if (token) {
      useAuthStore.getState().setAccessToken(token);
      return token;
    }
  } catch {
    /* fall through */
  }
  return null;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;

    const isAuthCall = original?.url?.includes("/auth/");
    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const token = await refreshing;
      refreshing = null;
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
      // Refresh failed — clear session.
      useAuthStore.getState().clear();
    }
    return Promise.reject(error);
  },
);

/** Extract a human-friendly message from an API error. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: { message?: string } } | undefined;
    return data?.error?.message || error.message || "Something went wrong.";
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}
