"use client";

import { useQuery } from "@tanstack/react-query";
import { listVoices } from "@/lib/api/voices";

export function useVoices(language?: string) {
  return useQuery({
    queryKey: ["voices", language ?? "all"],
    queryFn: () => listVoices(language),
  });
}
