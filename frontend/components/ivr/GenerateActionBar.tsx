interface GenerateActionBarProps {
  statusText: string;
  buttonLabel: string;
  buttonIcon: string;
  disabled: boolean;
  onClick: () => void;
}

export function GenerateActionBar({
  statusText,
  buttonLabel,
  buttonIcon,
  disabled,
  onClick,
}: GenerateActionBarProps) {
  return (
    <div className="fixed bottom-0 right-0 w-[calc(100%-16rem)] p-gutter glass-generate-bar z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-md text-xs text-on-surface-variant/60">
          <span>{statusText}</span>
        </div>
        <button
          type="button"
          onClick={onClick}
          disabled={disabled}
          className="bg-primary text-on-primary-container px-8 py-2.5 rounded-lg font-bold text-body-sm flex items-center gap-3 hover:opacity-90 active:scale-95 transition-all shadow-xl shadow-primary/10 tracking-tight disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
        >
          {buttonLabel}
          <span className="material-symbols-outlined !text-sm">{buttonIcon}</span>
        </button>
      </div>
    </div>
  );
}
