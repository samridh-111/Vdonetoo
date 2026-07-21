"use client";

let permissionRequested = false;

/** Requested lazily on the user's first "Generate" click, not on page load. */
export async function ensureNotificationPermission(): Promise<NotificationPermission | "unsupported"> {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "unsupported";
  }
  if (Notification.permission !== "default" || permissionRequested) {
    return Notification.permission;
  }
  permissionRequested = true;
  return Notification.requestPermission();
}

export function sendDesktopNotification(title: string, body?: string): void {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (Notification.permission !== "granted") return;
  new Notification(title, { body });
}
