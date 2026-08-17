"use client";

import { useQuery } from "@tanstack/react-query";
import { getBatchEstimate } from "@/lib/api/batch";

/** Pre-generation estimate, shown before the user ever clicks Generate --
 * distinct from the in-progress ETA (useBatchStatus), which only becomes
 * available once at least one job in the running batch has completed. */
export function useBatchEstimate(scriptCount: number, languageCount: number, enabled: boolean) {
  return useQuery({
    queryKey: ["batch-estimate", scriptCount, languageCount],
    queryFn: () => getBatchEstimate(scriptCount, languageCount),
    enabled: enabled && scriptCount > 0,
  });
}
