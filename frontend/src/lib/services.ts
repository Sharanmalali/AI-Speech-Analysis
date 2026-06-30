import { api } from "@/lib/api";
import type {
  AuthResponse,
  JobStatusResponse,
  JobWithAudio,
  Page,
  ResultResponse,
  UploadResponse,
  UserProfile,
} from "@/lib/types";

// --- Auth ------------------------------------------------------------------
export const authService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
    return data;
  },
  async register(email: string, password: string, fullName?: string): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    return data;
  },
  async exchangeSupabase(token: string): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>("/auth/supabase", {
      supabase_access_token: token,
    });
    return data;
  },
  async me(): Promise<UserProfile> {
    const { data } = await api.get<UserProfile>("/auth/me");
    return data;
  },
  async logout(): Promise<void> {
    await api.post("/auth/logout");
  },
};

// --- Upload ----------------------------------------------------------------
export const uploadService = {
  async upload(
    file: File,
    onProgress?: (pct: number) => void,
  ): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post<UploadResponse>("/audio/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    });
    return data;
  },
  streamUrl(audioFileId: string): string {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "";
    return `${base}/api/v1/audio/${audioFileId}/stream`;
  },
};

// --- Jobs ------------------------------------------------------------------
export const jobService = {
  async list(page = 1, pageSize = 20): Promise<Page<JobWithAudio>> {
    const { data } = await api.get<Page<JobWithAudio>>("/jobs", {
      params: { page, page_size: pageSize },
    });
    return data;
  },
  async get(jobId: string): Promise<JobWithAudio> {
    const { data } = await api.get<JobWithAudio>(`/jobs/${jobId}`);
    return data;
  },
  async status(jobId: string): Promise<JobStatusResponse> {
    const { data } = await api.get<JobStatusResponse>(`/jobs/${jobId}/status`);
    return data;
  },
  async cancel(jobId: string): Promise<JobStatusResponse> {
    const { data } = await api.post<JobStatusResponse>(`/jobs/${jobId}/cancel`);
    return data;
  },
  async remove(jobId: string): Promise<void> {
    await api.delete(`/jobs/${jobId}`);
  },
};

// --- Results ---------------------------------------------------------------
export const resultService = {
  async get(jobId: string): Promise<ResultResponse> {
    const { data } = await api.get<ResultResponse>(`/results/${jobId}`);
    return data;
  },
};

// --- Reports ---------------------------------------------------------------
export const reportService = {
  async generate(jobId: string) {
    const { data } = await api.post(`/reports/${jobId}/generate`);
    return data;
  },
  async download(jobId: string): Promise<Blob> {
    const { data } = await api.get(`/reports/${jobId}/download`, {
      responseType: "blob",
    });
    return data as Blob;
  },
};

// --- Demo ------------------------------------------------------------------
export const demoService = {
  async getSampleResult(): Promise<ResultResponse> {
    const { data } = await api.get<ResultResponse>("/demo/sample-result");
    return data;
  },
};
