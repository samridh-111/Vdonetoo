"use client";

import { useQuery } from "@tanstack/react-query";
import { getBatchStatus } from "@/lib/api/batch";

/** Polls every 5s as a belt-and-suspenders fallback alongside the WebSocket
 * stream (useBatchWebSocket) -- Redis pub/sub has no replay buffer, so this
 * covers the snapshot/WS-connect race window cheaply. */
export function useBatchStatus(batchId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["batch-status", batchId],
    queryFn: () => getBatchStatus(batchId as string),
    enabled: Boolean(batchId) && enabled,
    refetchInterval: 5000,
  });
}
