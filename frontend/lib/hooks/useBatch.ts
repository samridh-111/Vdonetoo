"use client";

import { useQuery } from "@tanstack/react-query";
import { getBatch } from "@/lib/api/batch";

export function useBatch(batchId: string | null) {
  return useQuery({
    queryKey: ["batch", batchId],
    queryFn: () => getBatch(batchId as string),
    enabled: Boolean(batchId),
  });
}
