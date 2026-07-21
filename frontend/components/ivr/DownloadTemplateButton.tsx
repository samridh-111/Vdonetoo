export function DownloadTemplateButton() {
  return (
    <a
      href="/templates/ivr_script_template.csv"
      download
      className="px-3 py-1.5 rounded bg-surface-container-high border minimal-divider text-on-surface text-body-sm font-medium flex items-center gap-2 hover:bg-surface-variant transition-colors"
    >
      <span className="material-symbols-outlined !text-[18px]">download</span>
      Download Template
    </a>
  );
}
