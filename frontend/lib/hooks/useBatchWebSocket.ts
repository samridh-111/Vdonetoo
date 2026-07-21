"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { wsUrl } from "@/lib/api/client";

const MAX_RECONNECT_DELAY_MS = 15000;

/** Every progress message just triggers a refetch of ['batch-status', id]
 * (the REST endpoint is the authoritative snapshot) rather than trying to
 * patch fine-grained state client-side from partial WS payloads. */
export function useBatchWebSocket(batchId: string | null, enabled: boolean): void {
  const queryClient = useQueryClient();
  const attemptRef = useRef(0);

  useEffect(() => {
    if (!batchId || !enabled) return;

    let socket: WebSocket | null = null;
    let closedByClient = false;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      socket = new WebSocket(wsUrl(`/ws/batch/${batchId}`));

      socket.onmessage = () => {
        queryClient.invalidateQueries({ queryKey: ["batch-status", batchId] });
      };

      socket.onopen = () => {
        attemptRef.current = 0;
      };

      socket.onclose = () => {
        if (closedByClient) return;
        attemptRef.current += 1;
        const delay = Math.min(1000 * 2 ** attemptRef.current, MAX_RECONNECT_DELAY_MS);
        reconnectTimeout = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      closedByClient = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      socket?.close();
    };
  }, [batchId, enabled, queryClient]);
}
