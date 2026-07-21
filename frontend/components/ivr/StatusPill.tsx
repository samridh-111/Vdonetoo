const STATUS_STYLES: Record<string, string> = {
  valid: "text-primary",
  error: "text-error",
  pending: "text-on-surface-variant",
  queued: "text-on-surface-variant",
  validating: "text-on-surface-variant",
  preparing: "text-on-surface-variant",
  translating: "text-primary",
  generating: "text-primary",
  uploading: "text-primary",
  retrying: "text-primary",
  completed: "text-primary",
  failed: "text-error",
  cancelled: "text-on-surface-variant",
};

const STATUS_LABELS: Record<string, string> = {
  valid: "Valid",
  error: "Error",
  pending: "Pending",
  queued: "Queued",
  validating: "Validating",
  preparing: "Preparing",
  translating: "Translating",
  generating: "Generating",
  uploading: "Uploading",
  retrying: "Retrying",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function StatusPill({ status }: { status: string }) {
  const colorClass = STATUS_STYLES[status] ?? "text-on-surface-variant";
  const label = STATUS_LABELS[status] ?? status;
  return <span className={`${colorClass} text-[10px] font-bold uppercase tracking-wider`}>{label}</span>;
}
