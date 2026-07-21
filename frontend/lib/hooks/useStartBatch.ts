"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startBatch } from "@/lib/api/batch";
import type { BatchSummary } from "@/lib/types/batch";

export function useStartBatch() {
  const queryClient = useQueryClient();
  return useMutation<BatchSummary, Error, string>({
    mutationFn: startBatch,
    onSuccess: (batch) => {
      queryClient.invalidateQueries({ queryKey: ["batch-status", batch.id] });
    },
  });
}
