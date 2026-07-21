import type { BatchDetail, BatchStatusOut, BatchSummary, TranslationMode } from "@/lib/types/batch";
import { API_URL, apiFetch } from "./client";

export interface CreateBatchPayload {
  upload_token: string;
  name: string;
  translation_mode: TranslationMode;
  target_languages: string[];
  translation_provider: "openai" | "gemini";
  default_voice_map: Record<string, string>;
  concurrency_limit?: number;
}

export interface CreateBatchResponse {
  batch_id: string;
  status: string;
  total_scripts: number;
}

export async function createBatch(payload: CreateBatchPayload): Promise<CreateBatchResponse> {
  return apiFetch<CreateBatchResponse>("/api/v1/batch/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function startBatch(batchId: string): Promise<BatchSummary> {
  return apiFetch<BatchSummary>("/api/v1/batch/start", {
    method: "POST",
    body: JSON.stringify({ batch_id: batchId }),
  });
}

export async function cancelBatch(batchId: string): Promise<BatchSummary> {
  return apiFetch<BatchSummary>("/api/v1/batch/cancel", {
    method: "POST",
    body: JSON.stringify({ batch_id: batchId }),
  });
}

export async function getBatch(batchId: string): Promise<BatchDetail> {
  return apiFetch<BatchDetail>(`/api/v1/batch/${batchId}`);
}

export async function getBatchStatus(batchId: string): Promise<BatchStatusOut> {
  return apiFetch<BatchStatusOut>(`/api/v1/batch/${batchId}/status`);
}

export function getDownloadUrl(batchId: string): string {
  return `${API_URL}/api/v1/batch/${batchId}/download`;
}
