"use client";

import { useEffect, useState } from "react";
import { SideNav } from "@/components/layout/SideNav";
import { TopAppBar } from "@/components/layout/TopAppBar";
import { UploadDropzone } from "@/components/ivr/UploadDropzone";
import { BatchPreviewTable, type PreviewRow } from "@/components/ivr/BatchPreviewTable";
import { VoiceSelectionList } from "@/components/ivr/VoiceSelectionList";
import { LanguageMappingList } from "@/components/ivr/LanguageMappingList";
import { SummaryStats } from "@/components/ivr/SummaryStats";
import { GenerateActionBar } from "@/components/ivr/GenerateActionBar";
import { DownloadTemplateButton } from "@/components/ivr/DownloadTemplateButton";
import { useUploadFile, useUploadGoogleSheet } from "@/lib/hooks/useUploadBatch";
import { useCreateBatch } from "@/lib/hooks/useCreateBatch";
import { useStartBatch } from "@/lib/hooks/useStartBatch";
import { useBatchStatus } from "@/lib/hooks/useBatchStatus";
import { useBatchWebSocket } from "@/lib/hooks/useBatchWebSocket";
import { getDownloadUrl } from "@/lib/api/batch";
import { showToast } from "@/lib/notifications/toast";
import { ensureNotificationPermission, sendDesktopNotification } from "@/lib/notifications/desktopNotify";
import type { UploadResponse } from "@/lib/types/upload";
import type { TranslationMode } from "@/lib/types/batch";
import type { Voice } from "@/lib/types/voice";

export default function IvrAutomationPage() {
  const [uploadToken, setUploadToken] = useState<string | null>(null);
  const [previewRows, setPreviewRows] = useState<PreviewRow[]>([]);
  const [translationMode, setTranslationMode] = useState<TranslationMode>("keep_original");
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchName] = useState(() => `Batch ${new Date().toISOString().slice(0, 10)}`);
  const [notifiedTerminal, setNotifiedTerminal] = useState(false);

  const uploadFile = useUploadFile();
  const uploadSheet = useUploadGoogleSheet();
  const createBatch = useCreateBatch();
  const startBatch = useStartBatch();

  const isProcessing = Boolean(batchId);
  const { data: status } = useBatchStatus(batchId, isProcessing);
  useBatchWebSocket(batchId, isProcessing);

  function applyUploadResult(result: UploadResponse) {
    setUploadToken(result.upload_token);
    setPreviewRows(
      result.rows.map((row) => ({
        key: String(row.row_index),
        externalId: row.external_id,
        scriptText: row.script_text,
        languages: row.detected_language_code ? [row.detected_language_code] : [],
        status: row.is_valid ? "valid" : "error",
      })),
    );
  }

  async function handleFileSelected(file: File) {
    try {
      const result = await uploadFile.mutateAsync(file);
      applyUploadResult(result);
      showToast({
        title: "File uploaded",
        description: `${result.valid_rows} of ${result.total_rows} rows are valid.`,
        variant: "success",
      });
    } catch (error) {
      showToast({ title: "Upload failed", description: (error as Error).message, variant: "error" });
    }
  }

  async function handleGoogleSheetSubmit(url: string) {
    try {
      const result = await uploadSheet.mutateAsync(url);
      applyUploadResult(result);
      showToast({
        title: "Sheet imported",
        description: `${result.valid_rows} of ${result.total_rows} rows are valid.`,
        variant: "success",
      });
    } catch (error) {
      showToast({ title: "Import failed", description: (error as Error).message, variant: "error" });
    }
  }

  function toggleLanguage(code: string) {
    setTargetLanguages((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
  }

  async function handleGenerateClick() {
    if (status?.status === "completed" && batchId) {
      window.location.href = getDownloadUrl(batchId);
      return;
    }

    if (!uploadToken) return;

    await ensureNotificationPermission();

    try {
      const languagesForVoiceMap = targetLanguages.length
        ? targetLanguages
        : Array.from(new Set(previewRows.flatMap((row) => row.languages)));
      const defaultVoiceMap = selectedVoice
        ? Object.fromEntries(languagesForVoiceMap.map((code) => [code, selectedVoice.preset_key]))
        : {};

      const created = await createBatch.mutateAsync({
        upload_token: uploadToken,
        name: batchName,
        translation_mode: translationMode,
        target_languages: targetLanguages,
        translation_provider: "openai",
        default_voice_map: defaultVoiceMap,
      });

      await startBatch.mutateAsync(created.batch_id);
      setBatchId(created.batch_id);
      setNotifiedTerminal(false);
      showToast({ title: "Batch started", description: "Generation is running in the background.", variant: "info" });
    } catch (error) {
      showToast({ title: "Could not start batch", description: (error as Error).message, variant: "error" });
    }
  }

  useEffect(() => {
    if (!status || notifiedTerminal) return;

    if (status.status === "completed") {
      setNotifiedTerminal(true);
      showToast({
        title: "Batch complete",
        description: `${status.completed_jobs} audio files generated${status.failed_jobs ? `, ${status.failed_jobs} failed` : ""}.`,
        variant: "success",
      });
      sendDesktopNotification("Batch complete", `${status.completed_jobs} audio files are ready to download.`);
    } else if (status.status === "failed") {
      setNotifiedTerminal(true);
      showToast({ title: "Batch failed", description: "See the batch logs for details.", variant: "error" });
      sendDesktopNotification("Batch failed", "The IVR batch could not complete. Check the logs.");
    }
  }, [status, notifiedTerminal]);

  const displayRows: PreviewRow[] = status?.scripts.length
    ? status.scripts.map((script) => {
        const languages = script.jobs.length
          ? script.jobs.map((job) => job.language_code)
          : script.detected_language_code
            ? [script.detected_language_code]
            : [];
        let rowStatus = script.status;
        if (script.jobs.length) {
          if (script.jobs.every((job) => job.stage === "completed")) rowStatus = "completed";
          else if (script.jobs.some((job) => job.stage === "failed")) rowStatus = "failed";
          else if (script.jobs.some((job) => job.stage === "retrying")) rowStatus = "retrying";
          else rowStatus = "generating";
        }
        return {
          key: script.id,
          externalId: script.external_id,
          scriptText: script.script_text,
          languages,
          status: rowStatus,
        };
      })
    : previewRows;

  const totalScripts = status?.total_scripts || previewRows.length;
  const languageCount = new Set(displayRows.flatMap((row) => row.languages)).size;
  const estimatedMinutes =
    status?.estimated_seconds_remaining != null ? Math.max(1, Math.round(status.estimated_seconds_remaining / 60)) : null;

  const isGenerating =
    isProcessing && status !== undefined && !["completed", "failed", "cancelled"].includes(status.status);
  const isCompleted = status?.status === "completed";

  let buttonLabel = "GENERATE IVRS";
  let buttonIcon = "bolt";
  if (isGenerating) {
    buttonLabel = "GENERATING...";
    buttonIcon = "hourglass_empty";
  } else if (isCompleted) {
    buttonLabel = "DOWNLOAD ZIP";
    buttonIcon = "download";
  }

  let statusText = "Upload a script sheet to get started.";
  if (previewRows.length > 0 && !isProcessing) {
    statusText = `${previewRows.length} scripts ready`;
  }
  if (status) {
    if (isGenerating) {
      const done = status.completed_jobs + status.failed_jobs;
      statusText = `${done}/${status.total_jobs} complete${estimatedMinutes != null ? ` · Est. ${estimatedMinutes}m remaining` : ""}`;
    } else if (isCompleted) {
      statusText = `Batch complete${status.failed_jobs ? ` · ${status.failed_jobs} failed` : ""}`;
    } else if (status.status === "failed") {
      statusText = "Batch failed";
    } else if (status.status === "cancelled") {
      statusText = "Batch cancelled";
    }
  }

  return (
    <>
      <SideNav />
      <main className="flex-1 ml-64 min-h-screen flex flex-col relative pb-32">
        <TopAppBar />

        <div className="p-gutter max-w-7xl mx-auto w-full space-y-xl">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight mb-1">IVR Automation</h2>
              <p className="font-body-lg text-on-surface-variant opacity-60">
                Configure and generate multi-lingual AI responses.
              </p>
            </div>
            <DownloadTemplateButton />
          </div>

          <div className="grid grid-cols-12 gap-xl">
            <div className="col-span-12 lg:col-span-8 space-y-xl">
              {!isProcessing && (
                <UploadDropzone
                  onFileSelected={handleFileSelected}
                  onGoogleSheetSubmit={handleGoogleSheetSubmit}
                  isUploading={uploadFile.isPending || uploadSheet.isPending}
                />
              )}

              <section className="space-y-md">
                <div className="flex items-center justify-between">
                  <h3 className="text-title-md font-medium text-on-surface">Batch Preview</h3>
                  <span className="flex items-center gap-2 text-xs font-medium text-on-surface-variant/60 uppercase tracking-widest">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${displayRows.length ? "bg-green-500" : "bg-on-surface-variant/30"}`}
                    />
                    {displayRows.length ? "Ready" : "No scripts yet"}
                  </span>
                </div>
                <BatchPreviewTable rows={displayRows} />
              </section>
            </div>

            <div className="col-span-12 lg:col-span-4 space-y-xl">
              <VoiceSelectionList selectedVoiceId={selectedVoice?.id ?? null} onSelect={setSelectedVoice} />
              <LanguageMappingList
                mode={translationMode}
                onModeChange={setTranslationMode}
                selectedLanguages={targetLanguages}
                onToggleLanguage={toggleLanguage}
              />
              <SummaryStats totalScripts={totalScripts} languageCount={languageCount} estimatedMinutes={estimatedMinutes} />
            </div>
          </div>
        </div>

        <GenerateActionBar
          statusText={statusText}
          buttonLabel={buttonLabel}
          buttonIcon={buttonIcon}
          disabled={(!uploadToken && !batchId) || createBatch.isPending || startBatch.isPending || isGenerating}
          onClick={handleGenerateClick}
        />
      </main>
    </>
  );
}
