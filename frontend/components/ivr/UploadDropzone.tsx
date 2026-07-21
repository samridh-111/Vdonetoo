"use client";

import { useRef, useState } from "react";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  onGoogleSheetSubmit: (url: string) => void;
  isUploading: boolean;
}

export function UploadDropzone({ onFileSelected, onGoogleSheetSubmit, isUploading }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showSheetInput, setShowSheetInput] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onFileSelected(file);
  }

  return (
    <section>
      <div
        className={`group border-2 border-dashed rounded-xl py-xl flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
          isDragging ? "border-primary bg-white/[0.02]" : "minimal-divider hover:border-white/20 hover:bg-white/[0.01]"
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className="w-10 h-10 rounded-lg bg-surface-container-high border minimal-divider flex items-center justify-center mb-md group-hover:bg-surface-container-highest transition-colors">
          <span className="material-symbols-outlined text-on-surface-variant">
            {isUploading ? "hourglass_empty" : "upload"}
          </span>
        </div>
        <h3 className="text-body-sm font-medium text-on-surface mb-1">
          {isUploading ? "Uploading..." : "Upload script sheet"}
        </h3>
        <p className="text-xs text-on-surface-variant/50">Drop .xlsx or .csv files here</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onFileSelected(file);
            event.target.value = "";
          }}
        />
      </div>

      <div className="mt-2 text-center">
        {showSheetInput ? (
          <form
            className="flex gap-2 justify-center"
            onSubmit={(event) => {
              event.preventDefault();
              if (sheetUrl.trim()) onGoogleSheetSubmit(sheetUrl.trim());
            }}
          >
            <input
              autoFocus
              value={sheetUrl}
              onChange={(event) => setSheetUrl(event.target.value)}
              placeholder="Paste a public Google Sheets link"
              className="flex-1 max-w-sm bg-surface-container-high border minimal-divider rounded text-body-sm text-on-surface px-2 py-1"
            />
            <button type="submit" className="text-body-sm text-primary font-medium">
              Import
            </button>
          </form>
        ) : (
          <button
            type="button"
            className="text-xs text-on-surface-variant/50 hover:text-primary transition-colors"
            onClick={() => setShowSheetInput(true)}
          >
            or paste a Google Sheets link
          </button>
        )}
      </div>
    </section>
  );
}
