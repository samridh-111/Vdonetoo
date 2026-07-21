import type { Script } from "./script";

export type TranslationMode =
  | "keep_original"
  | "translate_everything"
  | "translate_selected"
  | "generate_multiple";

export type BatchStatus = "draft" | "queued" | "processing" | "completed" | "failed" | "cancelled";

export interface BatchSummary {
  id: string;
  name: string;
  status: BatchStatus;
  total_scripts: number;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface BatchDetail extends BatchSummary {
  source_type: string;
  translation_mode: string;
  target_languages: string[];
  translation_provider: string;
  zip_storage_path: string | null;
  scripts: Script[];
}

export interface BatchStatusOut {
  id: string;
  status: BatchStatus;
  total_scripts: number;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  percent_complete: number;
  estimated_seconds_remaining: number | null;
  scripts: Script[];
}
