"use client";

import { useLanguages } from "@/lib/hooks/useLanguages";
import type { TranslationMode } from "@/lib/types/batch";

const MODE_OPTIONS: { value: TranslationMode; label: string }[] = [
  { value: "keep_original", label: "Keep Original" },
  { value: "translate_everything", label: "Translate Everything" },
  { value: "translate_selected", label: "Translate Selected Languages" },
  { value: "generate_multiple", label: "Generate Multiple Languages" },
];

interface LanguageMappingListProps {
  mode: TranslationMode;
  onModeChange: (mode: TranslationMode) => void;
  selectedLanguages: string[];
  onToggleLanguage: (code: string) => void;
}

export function LanguageMappingList({
  mode,
  onModeChange,
  selectedLanguages,
  onToggleLanguage,
}: LanguageMappingListProps) {
  const { data: languages = [] } = useLanguages();
  const showLanguagePicker = mode === "translate_selected" || mode === "generate_multiple";

  return (
    <section className="space-y-md">
      <h3 className="text-title-md font-medium text-on-surface">Language Mapping</h3>

      <select
        value={mode}
        onChange={(event) => onModeChange(event.target.value as TranslationMode)}
        className="w-full bg-surface-container-high border minimal-divider rounded text-body-sm text-on-surface px-2 py-1.5"
      >
        {MODE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {showLanguagePicker && (
        <div className="space-y-0.5">
          {languages.map((language, index) => {
            const isSelected = selectedLanguages.includes(language.code);
            return (
              <button
                type="button"
                key={language.code}
                onClick={() => onToggleLanguage(language.code)}
                className={`w-full flex items-center justify-between py-1.5 text-body-sm ${
                  index > 0 ? "border-t minimal-divider" : ""
                }`}
              >
                <span className="text-on-surface-variant/60">{language.name}</span>
                <span className={isSelected ? "text-primary font-medium" : "text-on-surface-variant/40"}>
                  {isSelected ? "Mapped" : "Not mapped"}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {mode === "translate_everything" && (
        <p className="text-[11px] text-on-surface-variant/50">
          Every supported language will be generated automatically.
        </p>
      )}
      {mode === "keep_original" && (
        <p className="text-[11px] text-on-surface-variant/50">
          Audio will be generated in each script&apos;s original detected language only.
        </p>
      )}
    </section>
  );
}
