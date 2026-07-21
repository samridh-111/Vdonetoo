import type { UploadResponse } from "@/lib/types/upload";
import { apiFetch } from "./client";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<UploadResponse>("/api/v1/upload", { method: "POST", body: formData });
}

export async function uploadGoogleSheet(url: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("google_sheet_url", url);
  return apiFetch<UploadResponse>("/api/v1/upload", { method: "POST", body: formData });
}
