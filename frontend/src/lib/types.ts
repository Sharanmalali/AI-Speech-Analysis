// API domain types mirroring the FastAPI backend schemas.

export type UserRole = "admin" | "doctor" | "user";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: UserProfile;
  tokens: TokenPair;
}

export type JobStatus =
  | "pending"
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export type JobStage =
  | "uploaded"
  | "noise_reduction"
  | "diarization"
  | "segmentation"
  | "transcription"
  | "translation"
  | "feature_extraction"
  | "gender_prediction"
  | "age_prediction"
  | "atypicality_classification"
  | "aggregation"
  | "report_generation"
  | "done";

export type Gender = "male" | "female" | "unknown";
export type AgeGroup = "child" | "teen" | "adult" | "senior" | "unknown";
export type AtypicalityLabel = "typical" | "atypical" | "unknown";

export interface AudioFileRead {
  id: string;
  original_filename: string;
  content_type: string;
  extension: string;
  size_bytes: number;
  duration_seconds: number | null;
  sample_rate: number | null;
  channels: number | null;
}

export interface JobStatusResponse {
  id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  detected_speakers?: number | null;
  error_message?: string | null;
}

export interface JobWithAudio {
  id: string;
  audio_file_id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  detected_speakers: number | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  processing_time_seconds: number | null;
  created_at: string;
  updated_at: string;
  audio_file: AudioFileRead;
}

export interface UploadResponse {
  audio_file_id: string;
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface TranscriptionRead {
  id: string;
  start_time: number;
  end_time: number;
  text_source: string | null;
  text_translated: string | null;
  confidence: number | null;
}

export interface PredictionRead {
  gender: Gender;
  gender_confidence: number | null;
  age_group: AgeGroup;
  age_confidence: number | null;
  raw_class_label: string | null;
  gender_age_source: "model" | "llm" | "hf";
  atypicality: AtypicalityLabel;
  atypicality_score: number | null;
  atypicality_confidence: number | null;
  features: Record<string, number> | null;
}

export interface SpeakerRead {
  id: string;
  label: string;
  diarization_id: string;
  color: string | null;
  total_speech_seconds: number;
  total_pause_seconds: number;
  segment_count: number;
  word_count: number;
  prediction: PredictionRead | null;
  transcriptions: TranscriptionRead[];
}

export interface AudioSummary {
  duration_seconds: number | null;
  sample_rate: number | null;
  channels: number | null;
  original_filename: string;
}

export interface ResultResponse {
  job_id: string;
  status: JobStatus;
  detected_speakers: number;
  language_source: string;
  language_target: string;
  processing_time_seconds: number | null;
  audio: AudioSummary;
  speakers: SpeakerRead[];
  has_report: boolean;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  error: { code: string; message: string; details?: unknown };
}
