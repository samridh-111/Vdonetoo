"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelBatch } from "@/lib/api/batch";
import type { BatchSummary } from "@/lib/types/batch";

export function useCancelBatch() {
  const queryClient = useQueryClient();
  return useMutation<BatchSummary, Error, string>({
    mutationFn: cancelBatch,
    onSuccess: (batch) => {
      queryClient.invalidateQueries({ queryKey: ["batch-status", batch.id] });
    },
  });
}
