"use client";

export type ToastVariant = "info" | "success" | "error";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
}

type Listener = (toast: ToastMessage) => void;

const listeners = new Set<Listener>();

export function onToast(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function showToast(toast: Omit<ToastMessage, "id">): void {
  const message: ToastMessage = { id: crypto.randomUUID(), ...toast };
  listeners.forEach((listener) => listener(message));
}
