"use client";

import { useMutation } from "@tanstack/react-query";
import { createBatch, type CreateBatchPayload, type CreateBatchResponse } from "@/lib/api/batch";

export function useCreateBatch() {
  return useMutation<CreateBatchResponse, Error, CreateBatchPayload>({ mutationFn: createBatch });
}
