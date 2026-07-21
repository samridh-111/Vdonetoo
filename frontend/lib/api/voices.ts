import type { Voice, VoicePreviewResponse } from "@/lib/types/voice";
import { apiFetch } from "./client";

export async function listVoices(language?: string): Promise<Voice[]> {
  const query = language ? `?language=${encodeURIComponent(language)}` : "";
  return apiFetch<Voice[]>(`/api/v1/voices${query}`);
}

export async function previewVoice(voiceId: string): Promise<VoicePreviewResponse> {
  return apiFetch<VoicePreviewResponse>(`/api/v1/voices/${voiceId}/preview`, { method: "POST" });
}
