interface SummaryStatsProps {
  totalScripts: number;
  languageCount: number;
  estimatedMinutes: number | null;
}

export function SummaryStats({ totalScripts, languageCount, estimatedMinutes }: SummaryStatsProps) {
  return (
    <section className="pt-xl space-y-md border-t minimal-divider">
      <div className="grid grid-cols-2 gap-md">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant/40 font-bold mb-1">
            Total Scripts
          </p>
          <p className="text-2xl font-light text-on-surface">{totalScripts.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant/40 font-bold mb-1">Languages</p>
          <p className="text-2xl font-light text-on-surface">{String(languageCount).padStart(2, "0")}</p>
        </div>
      </div>
      <p className="text-[11px] text-on-surface-variant/50">
        Estimated processing time:{" "}
        <span className="text-on-surface">
          {estimatedMinutes != null ? `${estimatedMinutes} minute${estimatedMinutes === 1 ? "" : "s"}` : "—"}
        </span>
      </p>
    </section>
  );
}
