export type JobStage =
  | "queued"
  | "preparing"
  | "translating"
  | "generating"
  | "uploading"
  | "completed"
  | "failed"
  | "retrying";

export interface Job {
  id: string;
  language_code: string;
  voice_id: string | null;
  stage: JobStage;
  attempt: number;
  max_attempts: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface Script {
  id: string;
  row_index: number;
  external_id: string | null;
  title: string | null;
  script_text: string;
  notes: string | null;
  detected_language_code: string | null;
  status: string;
  error_message: string | null;
  jobs: Job[];
}
