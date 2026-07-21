"use client";

import { useEffect, useState } from "react";
import { onToast, type ToastMessage } from "@/lib/notifications/toast";

const AUTO_DISMISS_MS = 5000;

export function Toaster() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    return onToast((toast) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, AUTO_DISMISS_MS);
    });
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 w-80">
      {toasts.map((toast) => {
        const borderClass =
          toast.variant === "error"
            ? "border-error/40"
            : toast.variant === "success"
              ? "border-primary/40"
              : "minimal-divider";
        return (
          <div
            key={toast.id}
            className={`rounded-lg border bg-surface-container-high px-4 py-3 shadow-xl text-body-sm ${borderClass}`}
          >
            <p className="font-medium text-on-surface">{toast.title}</p>
            {toast.description && (
              <p className="text-on-surface-variant/70 text-xs mt-0.5">{toast.description}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
