"use client";

import { useMutation } from "@tanstack/react-query";
import { uploadFile, uploadGoogleSheet } from "@/lib/api/upload";
import type { UploadResponse } from "@/lib/types/upload";

export function useUploadFile() {
  return useMutation<UploadResponse, Error, File>({ mutationFn: uploadFile });
}

export function useUploadGoogleSheet() {
  return useMutation<UploadResponse, Error, string>({ mutationFn: uploadGoogleSheet });
}
