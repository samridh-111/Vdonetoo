"use client";

import { useMutation } from "@tanstack/react-query";
import { previewVoice } from "@/lib/api/voices";
import type { VoicePreviewResponse } from "@/lib/types/voice";

export function useVoicePreview() {
  return useMutation<VoicePreviewResponse, Error, string>({ mutationFn: previewVoice });
}
