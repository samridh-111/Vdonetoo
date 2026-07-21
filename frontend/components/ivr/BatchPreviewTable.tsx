import { StatusPill } from "./StatusPill";

export interface PreviewRow {
  key: string;
  externalId: string | null;
  scriptText: string;
  languages: string[];
  status: string;
}

export function BatchPreviewTable({ rows }: { rows: PreviewRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="border-t minimal-divider py-xl text-center text-on-surface-variant/40 text-body-sm">
        No scripts uploaded yet.
      </div>
    );
  }

  return (
    <div className="border-t minimal-divider overflow-hidden overflow-x-auto">
      <table className="w-full text-left font-body-sm">
        <thead className="text-on-surface-variant/40 border-b minimal-divider">
          <tr>
            <th className="py-4 font-medium uppercase tracking-tighter text-[11px]">ID</th>
            <th className="py-4 font-medium uppercase tracking-tighter text-[11px]">Script Text</th>
            <th className="py-4 font-medium uppercase tracking-tighter text-[11px] text-center">Languages</th>
            <th className="py-4 font-medium uppercase tracking-tighter text-[11px] text-right">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y minimal-divider">
          {rows.map((row, index) => (
            <tr key={row.key} className="table-row group">
              <td className="py-4 text-on-surface-variant/60 font-mono text-xs">
                #{row.externalId ?? String(index + 1).padStart(3, "0")}
              </td>
              <td className="py-4 text-on-surface max-w-md truncate">{row.scriptText}</td>
              <td className="py-4">
                <div className="flex justify-center gap-1.5 flex-wrap">
                  {row.languages.length ? (
                    row.languages.map((lang) => (
                      <span
                        key={lang}
                        className="text-[10px] font-bold text-on-surface-variant/40 border minimal-divider px-1.5 py-0.5 rounded"
                      >
                        {lang.toUpperCase()}
                      </span>
                    ))
                  ) : (
                    <span className="text-[10px] text-on-surface-variant/30">—</span>
                  )}
                </div>
              </td>
              <td className="py-4 text-right">
                <StatusPill status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
